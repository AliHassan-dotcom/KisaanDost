import 'dart:typed_data';

/// Helper to wrap raw 16-bit Mono PCM audio bytes into a valid standard WAV (RIFF) container.
class WavHeaderHelper {
  const WavHeaderHelper._();

  /// Creates a standard 44-byte RIFF WAV header for raw 16-bit Mono PCM audio.
  static Uint8List createWavHeader({
    required int pcmByteLength,
    int sampleRate = 24000,
    int channels = 1,
    int bitsPerSample = 16,
  }) {
    final byteRate = sampleRate * channels * (bitsPerSample ~/ 8);
    final blockAlign = channels * (bitsPerSample ~/ 8);
    final totalDataLen = pcmByteLength;
    final totalAudioLen = totalDataLen + 36;

    final header = Uint8List(44);
    final buffer = ByteData.view(header.buffer);

    // 0-3: "RIFF"
    header[0] = 0x52; // R
    header[1] = 0x49; // I
    header[2] = 0x46; // F
    header[3] = 0x46; // F

    // 4-7: Size of the overall file minus 8 bytes
    buffer.setUint32(4, totalAudioLen, Endian.little);

    // 8-11: "WAVE"
    header[8] = 0x57;  // W
    header[9] = 0x41;  // A
    header[10] = 0x56; // V
    header[11] = 0x45; // E

    // 12-15: "fmt " subchunk
    header[12] = 0x66; // f
    header[13] = 0x6D; // m
    header[14] = 0x74; // t
    header[15] = 0x20; // ' '

    // 16-19: Subchunk1Size (16 for PCM)
    buffer.setUint32(16, 16, Endian.little);

    // 20-21: AudioFormat (1 for PCM)
    buffer.setUint16(20, 1, Endian.little);

    // 22-23: NumChannels (1 = mono, 2 = stereo)
    buffer.setUint16(22, channels, Endian.little);

    // 24-27: SampleRate
    buffer.setUint32(24, sampleRate, Endian.little);

    // 28-31: ByteRate (SampleRate * NumChannels * BitsPerSample/8)
    buffer.setUint32(28, byteRate, Endian.little);

    // 32-33: BlockAlign (NumChannels * BitsPerSample/8)
    buffer.setUint16(32, blockAlign, Endian.little);

    // 34-35: BitsPerSample (16 bits)
    buffer.setUint16(34, bitsPerSample, Endian.little);

    // 36-39: "data" subchunk header
    header[36] = 0x64; // d
    header[37] = 0x61; // a
    header[38] = 0x74; // t
    header[39] = 0x61; // a

    // 40-43: Subchunk2Size (NumSamples * NumChannels * BitsPerSample/8)
    buffer.setUint32(40, totalDataLen, Endian.little);

    return header;
  }

  /// Converts raw PCM bytes into playable WAV bytes by prefixing a 44-byte WAV header.
  static Uint8List pcmToWav(
    Uint8List pcmBytes, {
    int sampleRate = 24000,
    int channels = 1,
    int bitsPerSample = 16,
  }) {
    final header = createWavHeader(
      pcmByteLength: pcmBytes.length,
      sampleRate: sampleRate,
      channels: channels,
      bitsPerSample: bitsPerSample,
    );
    final wavBytes = Uint8List(header.length + pcmBytes.length);
    wavBytes.setRange(0, header.length, header);
    wavBytes.setRange(header.length, wavBytes.length, pcmBytes);
    return wavBytes;
  }
}
