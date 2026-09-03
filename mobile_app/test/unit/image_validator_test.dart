import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/utils/image_validator.dart';

void main() {
  group('ImageValidator', () {
    test('returns error when file is null', () {
      expect(ImageValidator.validate(file: null), 'No image selected');
    });

    test('returns error for missing file', () {
      expect(
        ImageValidator.validate(path: '/tmp/does_not_exist.jpg'),
        'Image file not found',
      );
    });

    test('returns error for unsupported extension', () {
      final file = File('${Directory.systemTemp.path}/scan.txt');
      file.writeAsStringSync('not an image');
      addTearDown(file.delete);
      expect(ImageValidator.validate(file: file), contains('Only JPG'));
    });

    test('returns error for empty file', () {
      final file = File('${Directory.systemTemp.path}/empty.jpg');
      file.writeAsBytesSync(<int>[]);
      addTearDown(file.delete);
      expect(ImageValidator.validate(file: file), 'Image file is empty');
    });
  });
}
