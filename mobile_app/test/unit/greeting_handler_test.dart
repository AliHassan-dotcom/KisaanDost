import 'package:flutter_test/flutter_test.dart';
import 'package:kisaan_dost/services/greeting_handler.dart';

void main() {
  group('GreetingHandler Unit Tests', () {
    test('Recognizes English greetings', () {
      expect(GreetingHandler.isGreeting('Hey'), isTrue);
      expect(GreetingHandler.isGreeting('Hi'), isTrue);
      expect(GreetingHandler.isGreeting('Hello'), isTrue);
      expect(GreetingHandler.isGreeting("What's up"), isTrue);
      expect(GreetingHandler.isGreeting('How are you'), isTrue);
      expect(GreetingHandler.isGreeting('Good morning'), isTrue);
      expect(GreetingHandler.isGreeting('Good afternoon'), isTrue);
      expect(GreetingHandler.isGreeting('Good evening'), isTrue);
      expect(GreetingHandler.isGreeting('Hello KisaanDost'), isTrue);
    });

    test('Recognizes Urdu & Roman Urdu greetings', () {
      expect(GreetingHandler.isGreeting('Assalamualaikum'), isTrue);
      expect(GreetingHandler.isGreeting('السلام علیکم'), isTrue);
      expect(GreetingHandler.isGreeting('Adaab'), isTrue);
      expect(GreetingHandler.isGreeting('آداب'), isTrue);
      expect(GreetingHandler.isGreeting('Kaise ho'), isTrue);
      expect(GreetingHandler.isGreeting('کیسے ہو'), isTrue);
      expect(GreetingHandler.isGreeting('Kya haal hai'), isTrue);
      expect(GreetingHandler.isGreeting('کیا حال ہے'), isTrue);
      expect(GreetingHandler.isGreeting('Salam KisaanDost'), isTrue);
    });

    test('Does NOT flag farming questions as greetings', () {
      expect(GreetingHandler.isGreeting('Pani kab lagana chahiye?'), isFalse);
      expect(GreetingHandler.isGreeting('گندم میں کھاد کب ڈالیں؟'), isFalse);
      expect(GreetingHandler.isGreeting('What is the price of wheat in Lahore?'), isFalse);
      expect(GreetingHandler.isGreeting('Spray Tilt 250 EC for yellow rust'), isFalse);
    });

    test('Provides exact specified English responses', () {
      final helloResp = GreetingHandler.getGreetingResponse('Hello');
      expect(helloResp.contains("I'm KisaanDost, your AI farming assistant"), isTrue);
      expect(helloResp.contains('How can I help you today?'), isTrue);

      final whatsUpResp = GreetingHandler.getGreetingResponse("What's up");
      expect(whatsUpResp.startsWith('Not much!'), isTrue);

      final howAreYouResp = GreetingHandler.getGreetingResponse('How are you');
      expect(howAreYouResp.startsWith("I'm great, thank you!"), isTrue);

      final goodMorningResp = GreetingHandler.getGreetingResponse('Good morning');
      expect(goodMorningResp.startsWith('Good morning!'), isTrue);
      expect(goodMorningResp.contains('Ready to help you with weather, pests, and crops'), isTrue);
    });

    test('Provides exact specified Urdu responses', () {
      final salamResp = GreetingHandler.getGreetingResponse('Assalamualaikum');
      expect(salamResp.startsWith('Walaikum Assalam!'), isTrue);
      expect(salamResp.contains('Main KisaanDost hoon, aapka AI farming assistant'), isTrue);
      expect(salamResp.contains('mausam, keede, fasal, aur mandi rates'), isTrue);

      final adaabResp = GreetingHandler.getGreetingResponse('Adaab');
      expect(adaabResp.startsWith('Adaab!'), isTrue);
      expect(adaabResp.contains('Main KisaanDost hoon'), isTrue);

      final kaiseHoResp = GreetingHandler.getGreetingResponse('Kaise ho');
      expect(kaiseHoResp.startsWith('Main theek hoon, shukriya!'), isTrue);

      final genericResp = GreetingHandler.getGreetingResponse('Kheriyat');
      expect(genericResp.contains('Main KisaanDost hoon'), isTrue);
    });
  });
}
