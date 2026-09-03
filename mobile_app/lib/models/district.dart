class District {
  const District({required this.name, this.normalizedName});

  final String name;
  final String? normalizedName;

  factory District.fromJson(String name) => District(name: name);

  @override
  String toString() => name;
}
