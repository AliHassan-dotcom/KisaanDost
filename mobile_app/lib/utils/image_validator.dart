import 'dart:io';

class ImageValidator {
  const ImageValidator._();

  static const int maxSizeBytes = 10 * 1024 * 1024; // 10 MB
  static const Set<String> allowedExtensions = <String>{
    'jpg',
    'jpeg',
    'png',
    'webp',
  };

  static String? validate({File? file, String? path}) {
    final target = file ?? (path != null ? File(path) : null);
    if (target == null) return 'No image selected';
    if (!target.existsSync()) return 'Image file not found';

    final ext = target.path.split('.').last.toLowerCase();
    if (!allowedExtensions.contains(ext)) {
      return 'Only JPG, PNG, or WEBP images are allowed';
    }

    final size = target.lengthSync();
    if (size > maxSizeBytes) {
      return 'Image must be smaller than 10 MB';
    }
    if (size == 0) return 'Image file is empty';

    return null;
  }
}
