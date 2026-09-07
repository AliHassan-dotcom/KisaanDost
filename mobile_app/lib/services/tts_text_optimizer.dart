/// Text optimizer for text-to-speech engines to achieve maximum pronunciation clarity.
class TtsTextOptimizer {
  static String optimize(String text) {
    if (text.isEmpty) return text;

    // Step 1: Replace Urdu script with Roman Urdu phonetics
    text = text.replaceAll('اسلام و علیکم', 'Assalamualaikum');
    text = text.replaceAll('اسلام علیکم', 'Assalamualaikum');
    text = text.replaceAll('السلام علیکم', 'Assalamualaikum');
    text = text.replaceAll('آج', 'Aaj');
    text = text.replaceAll('موسم', 'mausam');
    text = text.replaceAll('صاف', 'saaf');
    text = text.replaceAll('بارش', 'barish');
    text = text.replaceAll('سپرے', 'spray');
    text = text.replaceAll('اسپرے', 'spray');
    text = text.replaceAll('کھاد', 'khaad');
    text = text.replaceAll('پیداوار', 'paidaawar');
    text = text.replaceAll('فی', 'fi');
    text = text.replaceAll('ہے', 'hai');
    text = text.replaceAll('ہیں', 'hain');
    text = text.replaceAll('امکان', 'imkaan');
    text = text.replaceAll('خرچہ', 'kharcha');
    text = text.replaceAll('روپے', 'rupay');
    text = text.replaceAll('روپیہ', 'rupay');
    text = text.replaceAll('منڈی', 'mandi');
    text = text.replaceAll('لاہور', 'Lahore');
    text = text.replaceAll('گندم', 'Gandum');
    text = text.replaceAll('کپاس', 'Kapaas');
    text = text.replaceAll('چاول', 'Chawal');
    text = text.replaceAll('کماد', 'Kamaad');
    text = text.replaceAll('مکئی', 'Makai');
    text = text.replaceAll('ایکڑ', 'acre');
    text = text.replaceAll('کلو', 'kilo');
    text = text.replaceAll('صبح', 'subah');
    text = text.replaceAll('شام', 'shaam');
    text = text.replaceAll('درمیان', 'darmiyan');
    text = text.replaceAll('بیچ', 'bech');
    text = text.replaceAll('دیں', 'dein');
    text = text.replaceAll('کریں', 'karein');
    text = text.replaceAll('مدد', 'madad');
    text = text.replaceAll('مائیک', 'mic');
    text = text.replaceAll('دبائیں', 'dabayein');

    // Step 2: Replace symbols with words
    text = text.replaceAll('°C', ' degrees');
    text = text.replaceAll('°', ' degrees');
    text = text.replaceAll('%', ' percent');
    text = text.replaceAll('Rs.', ' rupay ');
    text = text.replaceAll('PKR', ' rupay ');
    text = text.replaceAll('/', ' per ');
    text = text.replaceAll('+', ' plus ');
    text = text.replaceAll('-', ' minus ');

    // Step 3: Add pauses for natural speech cadence
    text = text.replaceAll('۔', ',, ');
    text = text.replaceAll('،', ', ');
    text = text.replaceAll('.', ',, ');
    text = text.replaceAll('!', ',, ');

    // Step 4: Break long sentences with commas for breathing pauses
    if (text.length > 200) {
      text = text.replaceAll(' aur ', ',, aur ,, ');
      text = text.replaceAll(' lekin ', ',, lekin ,, ');
      text = text.replaceAll(' isliye ', ',, isliye ,, ');
    }

    // Clean up excessive whitespace and double commas
    text = text.replaceAll(RegExp(r',,+'), ',,');
    text = text.replaceAll(RegExp(r'\s+'), ' ').trim();

    // Step 5: Ensure proper capitalization for sentence flow
    text = text.replaceAll(RegExp(r'\baaj\b', caseSensitive: false), 'Aaj');
    text = text.replaceAll(RegExp(r'\bkal\b', caseSensitive: false), 'Kal');
    text = text.replaceAll(RegExp(r'\bassalam\s*o?\s*alaikum\b', caseSensitive: false), 'Assalamualaikum');

    return text;
  }
}
