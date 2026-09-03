import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/utils/validators.dart';

void main() {
  group('Validators', () {
    test('phone rejects empty input', () {
      expect(Validators.phone(null), isNotNull);
      expect(Validators.phone(''), isNotNull);
    });

    test('phone rejects too few digits', () {
      expect(Validators.phone('12345'), isNotNull);
    });

    test('phone accepts valid phone', () {
      expect(Validators.phone('03001001000'), isNull);
      expect(Validators.phone('+92 300 100 1000'), isNull);
    });

    test('password rejects short input', () {
      expect(Validators.password('12345'), isNotNull);
    });

    test('password accepts 6+ characters', () {
      expect(Validators.password('secret123'), isNull);
    });

    test('name rejects empty input', () {
      expect(Validators.name(''), isNotNull);
      expect(Validators.name('   '), isNotNull);
    });

    test('farmSize accepts null/empty', () {
      expect(Validators.farmSize(null), isNull);
      expect(Validators.farmSize(''), isNull);
    });

    test('farmSize rejects invalid values', () {
      expect(Validators.farmSize('abc'), isNotNull);
      expect(Validators.farmSize('0'), isNotNull);
      expect(Validators.farmSize('2001'), isNotNull);
    });
  });
}
