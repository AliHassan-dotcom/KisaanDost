import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/utils/wav_header_helper.dart';

void main() {
  group('WavHeaderHelper Unit Tests', () {
    test('createWavHeader generates valid 44-byte standard RIFF header', () {
      final header = WavHeaderHelper.createWavHeader(
        pcmByteLength: 1000,
        sampleRate: 24000,
        channels: 1,
        bitsPerSample: 16,
      );

      expect(header.length, equals(44));

      // RIFF marker
      expect(String.fromCharCodes(header.sublist(0, 4)), equals('RIFF'));

      // WAVE marker
      expect(String.fromCharCodes(header.sublist(8, 12)), equals('WAVE'));

      // fmt marker
      expect(String.fromCharCodes(header.sublist(12, 16)), equals('fmt '));

      // data marker
      expect(String.fromCharCodes(header.sublist(36, 40)), equals('data'));

      // Sample Rate check at byte 24
      final byteData = ByteData.view(header.buffer);
      expect(byteData.getUint32(24, Endian.little), equals(24000));
    });

    test('pcmToWav prefixes WAV header to raw PCM bytes', () {
      final rawPcm = Uint8List.fromList(List<int>.generate(200, (i) => i % 256));
      final wavBytes = WavHeaderHelper.pcmToWav(
        rawPcm,
        sampleRate: 16000,
      );

      expect(wavBytes.length, equals(44 + 200));
      expect(wavBytes.sublist(44), equals(rawPcm));
    });
  });
}
