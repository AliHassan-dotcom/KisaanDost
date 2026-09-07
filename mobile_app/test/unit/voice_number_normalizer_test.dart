import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/services/voice_assistant_engine.dart';

void main() {
  group('VoiceAssistantEngine Number Normalization', () {
    test('converts basic single and double digit numbers to Urdu words', () {
      expect(VoiceAssistantEngine.numberToUrduWords(0), 'صفر');
      expect(VoiceAssistantEngine.numberToUrduWords(5), 'پانچ');
      expect(VoiceAssistantEngine.numberToUrduWords(11), 'گیارہ');
      expect(VoiceAssistantEngine.numberToUrduWords(28), 'اٹھائیس');
      expect(VoiceAssistantEngine.numberToUrduWords(49), 'انچاس');
      expect(VoiceAssistantEngine.numberToUrduWords(99), 'ننانوے');
    });

    test('converts hundreds and thousands to Urdu words', () {
      expect(VoiceAssistantEngine.numberToUrduWords(100), 'ایک سو');
      expect(VoiceAssistantEngine.numberToUrduWords(200), 'دو سو');
      expect(VoiceAssistantEngine.numberToUrduWords(425), 'چار سو پچیس');
      expect(VoiceAssistantEngine.numberToUrduWords(1550), 'ایک ہزار پانچ سو پچاس');
      expect(VoiceAssistantEngine.numberToUrduWords(3850), 'تین ہزار آٹھ سو پچاس');
      expect(VoiceAssistantEngine.numberToUrduWords(8400), 'آٹھ ہزار چار سو');
      expect(VoiceAssistantEngine.numberToUrduWords(11200), 'گیارہ ہزار دو سو');
      expect(VoiceAssistantEngine.numberToUrduWords(150000), 'ایک لاکھ پچاس ہزار');
    });

    test('humanizeForSpeech converts 11200 and currency without dollars or english words', () {
      final input1 = '11200 روپے';
      final output1 = VoiceAssistantEngine.humanizeForSpeech(input1);
      expect(output1, contains('گیارہ ہزار دو سو'));
      expect(output1, contains('روپے'));
      expect(output1.toLowerCase(), isNot(contains('dollar')));

      final input2 = 'باسمتی چاول کا ریٹ 11,200 روپے فی 40 کلو ہے';
      final output2 = VoiceAssistantEngine.humanizeForSpeech(input2);
      expect(output2, contains('گیارہ ہزار دو سو'));
      expect(output2, contains('چالیس'));
      expect(output2.toLowerCase(), isNot(contains('dollar')));
    });

    test('humanizeForSpeech converts temperature, percentages, and pesticide dosages', () {
      final input = 'درجہ حرارت 28°C ہے، بارش کا امکان 49% ہے، اور 200ml فی ایکڑ اسپرے کریں۔';
      final output = VoiceAssistantEngine.humanizeForSpeech(input);
      expect(output, contains('اٹھائیس'));
      expect(output, contains('ڈگری سینٹی گریڈ'));
      expect(output, contains('انچاس'));
      expect(output, contains('فیصد'));
      expect(output, contains('دو سو'));
      expect(output, contains('ملی لیٹر'));
    });
  });
}
