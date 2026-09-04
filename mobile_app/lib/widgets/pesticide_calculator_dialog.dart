import 'package:flutter/material.dart';

class PesticideCalculatorDialog extends StatefulWidget {
  const PesticideCalculatorDialog({
    super.key,
    required this.crop,
    required this.pest,
    required this.solution,
    required this.dosePerAcre,
    required this.waterPerAcre,
    required this.costPerAcre,
    required this.timing,
    required this.isUrdu,
  });

  final String crop;
  final String pest;
  final String solution;
  final String dosePerAcre;
  final int waterPerAcre;
  final int costPerAcre;
  final String timing;
  final bool isUrdu;

  @override
  State<PesticideCalculatorDialog> createState() => _PesticideCalculatorDialogState();
}

class _PesticideCalculatorDialogState extends State<PesticideCalculatorDialog> {
  double _acres = 1.0;
  final TextEditingController _controller = TextEditingController(text: '1');

  void _updateAcres(String val) {
    final parsed = double.tryParse(val);
    if (parsed != null && parsed > 0) {
      setState(() => _acres = parsed);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isUrdu = widget.isUrdu;
    final totalWater = (widget.waterPerAcre * _acres).round();
    final totalCost = (widget.costPerAcre * _acres).round();
    final numTanks20L = totalWater > 0 ? (totalWater / 20).ceil() : 0;

    return Dialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
      backgroundColor: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              // Header
              Row(
                children: <Widget>[
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: const Color(0xFFE8F5E9),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: const Icon(Icons.calculate_outlined, color: Color(0xFF2E7D32), size: 24),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          isUrdu ? 'اسپرے اور دوائی کیلکولیٹر' : 'Pesticide & Spray Calculator',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Color(0xFF1B382B)),
                        ),
                        Text(
                          '${widget.crop} · ${widget.pest.split('(')[0]}',
                          style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // Acreage Input Slider & Field
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: const Color(0xFFF4F7F4),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Colors.green.shade100),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: <Widget>[
                        Text(
                          isUrdu ? 'رقبہ (ایکڑ):' : 'Farm Acreage (Acres):',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Color(0xFF1B382B)),
                        ),
                        SizedBox(
                          width: 80,
                          child: TextField(
                            controller: _controller,
                            keyboardType: const TextInputType.numberWithOptions(decimal: true),
                            onChanged: _updateAcres,
                            textAlign: TextAlign.center,
                            style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF2E7D32)),
                            decoration: InputDecoration(
                              contentPadding: const EdgeInsets.symmetric(vertical: 6, horizontal: 8),
                              isDense: true,
                              border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Slider(
                      value: _acres.clamp(1.0, 25.0),
                      min: 1.0,
                      max: 25.0,
                      divisions: 24,
                      activeColor: const Color(0xFF2E7D32),
                      inactiveColor: Colors.green.shade100,
                      onChanged: (val) {
                        setState(() {
                          _acres = val;
                          _controller.text = val.toStringAsFixed(val.truncateToDouble() == val ? 0 : 1);
                        });
                      },
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Results Grid
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Colors.grey.shade200),
                  boxShadow: const <BoxShadow>[
                    BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, 2)),
                  ],
                ),
                child: Column(
                  children: <Widget>[
                    _buildResultRow(
                      icon: Icons.sanitizer,
                      title: isUrdu ? 'تجویز کردہ دوا' : 'Pesticide Formula',
                      value: widget.solution,
                      color: const Color(0xFF2E7D32),
                    ),
                    const Divider(height: 16),
                    _buildResultRow(
                      icon: Icons.water_drop,
                      title: isUrdu ? 'کل پانی کی ضرورت' : 'Total Water Volume',
                      value: totalWater > 0 ? '$totalWater Liters ($numTanks20L tanks of 20L)' : 'Broadcast in standing water',
                      color: const Color(0xFF0277BD),
                    ),
                    const Divider(height: 16),
                    _buildResultRow(
                      icon: Icons.monetization_on_outlined,
                      title: isUrdu ? 'تخمینہ لاگت' : 'Estimated Cost',
                      value: 'Rs. ${totalCost.toString().replaceAllMapped(RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'), (m) => '${m[1]},')}',
                      color: Colors.orange.shade900,
                    ),
                    const Divider(height: 16),
                    _buildResultRow(
                      icon: Icons.access_time,
                      title: isUrdu ? 'اسپرے کا وقت' : 'Spray Timing',
                      value: widget.timing,
                      color: Colors.grey.shade800,
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 18),

              // Action Button
              ElevatedButton(
                onPressed: () => Navigator.pop(context),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF2E7D32),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                ),
                child: Text(
                  isUrdu ? 'ٹھیک ہے (بند کریں)' : 'Done',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildResultRow({
    required IconData icon,
    required String title,
    required String value,
    required Color color,
  }) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Icon(icon, size: 18, color: color),
        const SizedBox(width: 8),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(title, style: TextStyle(fontSize: 11, color: Colors.grey.shade600)),
              const SizedBox(height: 2),
              Text(value, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: color)),
            ],
          ),
        ),
      ],
    );
  }
}
