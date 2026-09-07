/// Intelligent Greeting Handler for KisaanDost Voice Assistant.
/// Recognizes English, Urdu, and Roman Urdu greetings and provides tailored, polite responses.
class GreetingHandler {
  /// Detects whether the input text is a greeting
  static bool isGreeting(String text) {
    final clean = _normalize(text);
    if (clean.isEmpty) return false;

    // Check if the query contains clear agricultural intent first (so we don't intercept actual questions)
    if (_hasAgriIntent(clean)) {
      // If it's a greeting combined with a question, treat as question unless it's only a greeting
      if (clean.split(' ').length > 4) {
        return false;
      }
    }

    // English greeting patterns
    final isEnglishGreeting = RegExp(
      r'^(hey|hi|hello|heyy|heya|hiya|howdy|what\x27?s\s+up|wassup|sup|what\s+is\s+up|how\s+are\s+you|how\s+r\s+u|how\s+are\s+u|how\s+do\s+you\s+do|good\s+morning|morning|good\s+afternoon|good\s+evening|good\s+day)(\s+(kisaandost|kisaan\s+dost|friend|there|bro|sir|ji))?[\s!.,?]*$',
      caseSensitive: false,
    ).hasMatch(clean);

    // Urdu & Roman Urdu greeting patterns
    final isUrduGreeting = RegExp(
      r'^(assalam\s*o?\s*alaikum|assalamualaikum|aslam\s*o?\s*alikum|salam|slam|adaab|adab|kaise\s+ho|kese\s+ho|kaise\s+hain|kese\s+hain|kya\s+haal\s+hai|kya\s+hal\s+hai|kya\s+haal\s+hy|kya\s+hal\s+hy|sab\s+theek|kheriyat)(\s+(kisaandost|kisaan\s+dost|bhai|ji|sahab))?[\s!.,?]*$',
      caseSensitive: false,
    ).hasMatch(clean) ||
        clean == 'اسلام علیکم' ||
        clean == 'السلام علیکم' ||
        clean == 'اسلام و علیکم' ||
        clean == 'سلام' ||
        clean == 'آداب' ||
        clean == 'کیسے ہو' ||
        clean == 'کیسے ہیں' ||
        clean == 'کیا حال ہے' ||
        clean == 'خیریت';

    return isEnglishGreeting || isUrduGreeting;
  }

  /// Returns the customized, friendly greeting response with self-introduction and offer of help
  static String getGreetingResponse(String input) {
    final clean = _normalize(input);

    // 1. English: "Good morning"
    if (RegExp(r'\bgood\s+morning\b', caseSensitive: false).hasMatch(clean) ||
        RegExp(r'\bmorning\b', caseSensitive: false).hasMatch(clean)) {
      return "Good morning! I'm KisaanDost, your AI farming assistant. Ready to help you with weather, pests, and crops. How can I assist?";
    }

    // 2. English: "Good afternoon"
    if (RegExp(r'\bgood\s+afternoon\b', caseSensitive: false).hasMatch(clean)) {
      return "Good afternoon! I'm KisaanDost, your AI farming assistant. Ready to help you with weather, pests, and crops. How can I assist?";
    }

    // 3. English: "Good evening"
    if (RegExp(r'\bgood\s+evening\b', caseSensitive: false).hasMatch(clean)) {
      return "Good evening! I'm KisaanDost, your AI farming assistant. Ready to help you with weather, pests, and crops. How can I assist?";
    }

    // 4. English: "What's up"
    if (RegExp(r'\b(what\x27?s\s+up|wassup|sup|what\s+is\s+up)\b', caseSensitive: false).hasMatch(clean)) {
      return "Not much! I'm KisaanDost, your AI farming assistant. I help farmers with weather, pests, and market rates. What can I do for you today?";
    }

    // 5. English: "How are you"
    if (RegExp(r'\b(how\s+are\s+you|how\s+r\s+u|how\s+are\s+u|how\s+do\s+you\s+do)\b', caseSensitive: false).hasMatch(clean)) {
      return "I'm great, thank you! I'm KisaanDost, your AI farming assistant. How can I help you with farming today?";
    }

    // 6. English: "Hey", "Hi", "Hello"
    if (RegExp(r'\b(hey|hi|hello|heya|hiya|howdy)\b', caseSensitive: false).hasMatch(clean)) {
      return "Hello! I'm KisaanDost, your AI farming assistant. I can help you with weather, pests, crops, and market rates. How can I help you today?";
    }

    // 7. Urdu: "Adaab" / "آداب"
    if (RegExp(r'\b(adaab|adab)\b', caseSensitive: false).hasMatch(clean) || clean.contains('آداب')) {
      return "Adaab! Main KisaanDost hoon, aapka AI farming assistant. Main aapki madad kar sakta hoon mausam, keede, fasal, aur mandi rates mein. Kya madad chahiye?";
    }

    // 8. Urdu: "Kaise ho" / "Kya haal hai"
    if (RegExp(r'\b(kaise\s+ho|kese\s+ho|kaise\s+hain|kese\s+hain|kya\s+haal\s+hai|kya\s+hal\s+hai|kya\s+haal\s+hy|kya\s+hal\s+hy|kheriyat)\b', caseSensitive: false).hasMatch(clean) ||
        clean.contains('کیسے ہو') ||
        clean.contains('کیسے ہیں') ||
        clean.contains('کیا حال') ||
        clean.contains('خیریت')) {
      return "Main theek hoon, shukriya! Main KisaanDost hoon, aapka AI farming assistant. Main aapki madad kar sakta hoon mausam, keede, fasal, aur mandi rates mein. Kya madad chahiye?";
    }

    // 9. Urdu: "Assalamualaikum" / "Salam"
    if (RegExp(r'\b(assalam\w*|salam\w*|slam\w*|aslam\w*)\b', caseSensitive: false).hasMatch(clean) ||
        clean.toLowerCase().contains('salam') ||
        clean.contains('سلام') ||
        clean.contains('اسلام')) {
      return "Walaikum Assalam! Main KisaanDost hoon, aapka AI farming assistant. Main aapki madad kar sakta hoon mausam, keede, fasal, aur mandi rates mein. Aaj main aapki kaise madad karun?";
    }

    // 10. Fallback greeting
    return "Assalamualaikum! Main KisaanDost hoon, aapka AI farming assistant. Kaise help karun?";
  }

  static String _normalize(String text) {
    return text.trim().replaceAll(RegExp(r'[\s]+'), ' ');
  }

  static bool _hasAgriIntent(String text) {
    final lower = text.toLowerCase();
    return RegExp(r'\b(pani|spray|khad|khaad|kangi|rust|mandi|rate|weather|mausam|keera|fasal|gandum|fertilizer|irrigate)\b')
        .hasMatch(lower);
  }
}
