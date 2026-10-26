"""SCMS-F013: attach up to 3 images (max 5 MB each) to a complaint.

Rules (SRS 4.2, SAD 4.3 / 6):
  * at most MAX_PHOTOS images per complaint, counting ones already attached
  * each image at most MAX_PHOTO_BYTES
  * files that break a rule are rejected with a clear message, and nothing is saved
    (all-or-nothing: one bad file rejects the whole request)

The limits are enforced here, on the server. The F010 "lodge complaint" endpoint can reuse
`attach_photos(complaint, request.files.getlist("photos"))` so both paths share one rule set.
"""
import uuid
from io import BytesIO
from pathlib import Path

from flask import current_app
from PIL import Image
from werkzeug.utils import secure_filename

from ..models import ComplaintPhoto

# Real image format (detected by Pillow, not trusted from the file name) -> extension
ALLOWED_FORMATS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}
MIME_TYPES = {".jpg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}


class PhotoError(Exception):
    """Carries what the API needs to build the SAD 4.4 error body."""

    def __init__(self, code, message, status, details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details or {}


def upload_root():
    """Upload folder; a relative UPLOAD_FOLDER is resolved from the project root."""
    folder = Path(current_app.config["UPLOAD_FOLDER"])
    if not folder.is_absolute():
        folder = Path(current_app.root_path).parent / folder
    return folder


def photo_path(photo):
    """Absolute path of a stored photo; refuses anything outside the upload folder."""
    root = upload_root().resolve()
    path = (root / photo.filename).resolve()
    if root not in path.parents:
        raise PhotoError("NOT_FOUND", "Photo not found.", 404)
    return path


def _read_and_validate(storage):
    """Return (bytes, extension) for one uploaded file, or raise PhotoError."""
    name = storage.filename
    limit = current_app.config["MAX_PHOTO_BYTES"]

    data = storage.stream.read(limit + 1)  # never read more than limit + 1 bytes
    if len(data) > limit:
        raise PhotoError(
            "PHOTO_TOO_LARGE",
            f"'{name}' is larger than {limit // (1024 * 1024)} MB.",
            413, {"file": name, "maxBytes": limit})
    if not data:
        raise PhotoError("INVALID_PHOTO", f"'{name}' is empty.", 422, {"file": name})

    try:
        with Image.open(BytesIO(data)) as img:
            img_format = img.format
            img.verify()  # catches truncated or corrupt images
    except (OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        raise PhotoError("INVALID_PHOTO", f"'{name}' is not a valid image file.",
                         422, {"file": name})

    if img_format not in ALLOWED_FORMATS:
        raise PhotoError("INVALID_PHOTO",
                         f"'{name}' must be a JPEG, PNG or WebP image.",
                         422, {"file": name, "allowed": sorted(ALLOWED_FORMATS)})
    return data, ALLOWED_FORMATS[img_format]


def attach_photos(complaint, files):
    """Validate `files` and attach them to `complaint`.

    Writes the files to disk and adds ComplaintPhoto rows to the session; the CALLER
    commits. If the commit fails, call `remove_files(rows)` to clean up the disk.
    Returns the new ComplaintPhoto rows.
    """
    files = [f for f in files if f and f.filename]  # browsers send an empty part if no file
    if not files:
        raise PhotoError("VALIDATION_ERROR", "Choose at least one photo to attach.", 422)

    max_photos = current_app.config["MAX_PHOTOS"]
    already = len(complaint.photos)
    if already + len(files) > max_photos:
        raise PhotoError(
            "TOO_MANY_PHOTOS",
            f"A complaint can have at most {max_photos} photos "
            f"({already} already attached, {len(files)} sent).",
            413, {"maxPhotos": max_photos, "alreadyAttached": already, "sent": len(files)})

    # Validate everything first, so one bad file means nothing is written.
    checked = [(f, *_read_and_validate(f)) for f in files]

    folder = upload_root() / complaint.public_id
    folder.mkdir(parents=True, exist_ok=True)

    rows, written = [], []
    try:
        for storage, data, ext in checked:
            stored_name = f"{uuid.uuid4().hex}{ext}"  # never use the user's file name on disk
            (folder / stored_name).write_bytes(data)
            written.append(folder / stored_name)
            row = ComplaintPhoto(
                filename=f"{complaint.public_id}/{stored_name}",
                original_name=(secure_filename(storage.filename) or f"photo{ext}")[:255],
                size_bytes=len(data))
            complaint.photos.append(row)
            rows.append(row)
    except Exception:
        for path in written:
            path.unlink(missing_ok=True)
        raise
    return rows


def remove_files(rows):
    """Delete the files of photo rows (used when a database commit fails)."""
    for row in rows:
        try:
            photo_path(row).unlink(missing_ok=True)
        except PhotoError:
            pass
