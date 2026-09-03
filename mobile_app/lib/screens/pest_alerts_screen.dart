import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/advisory.dart';
import '../models/pest_alert.dart';
import '../models/pest_citation.dart';
import '../models/pest_source.dart';
import '../providers/pest_provider.dart';
import '../providers/profile_provider.dart';
import '../widgets/kd_app_bar.dart';
import '../widgets/safety_notice.dart';
import '../widgets/status_badge.dart';

class PestAlertsScreen extends ConsumerWidget {
  const PestAlertsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pestAsync = ref.watch(pestProvider);
    final profileAsync = ref.watch(profileProvider);

    return Scaffold(
      appBar: KdAppBar(
        title: 'Pest Alerts',
        actions: <Widget>[
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              final district = profileAsync.value?.district ?? 'Lahore';
              ref.read(pestProvider.notifier).loadAlerts(district: district);
            },
          ),
        ],
      ),
      body: pestAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => Center(child: Text('Error: $error')),
        data: (state) => Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              _DistrictHeader(district: state.district),
              const SizedBox(height: 16),
              Expanded(
                child: ListView(
                  children: <Widget>[
                    if (state.alerts.isEmpty)
                      const Card(
                        child: Padding(
                          padding: EdgeInsets.all(16),
                          child: Text(
                            'No active pest alerts for your district. Reports will appear here once the pesticide data is ingested.',
                          ),
                        ),
                      )
                    else
                      ...state.alerts.map(
                        (alert) => _AlertCard(alert: alert),
                      ),
                    if (state.advisory != null)
                      _AdvisoryCard(advisory: state.advisory!),
                    if (state.sources.isNotEmpty)
                      _SourcesSection(sources: state.sources),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _DistrictHeader extends StatelessWidget {
  const _DistrictHeader({required this.district});

  final String district;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: <Widget>[
        Icon(Icons.location_on, color: Theme.of(context).colorScheme.primary),
        const SizedBox(width: 8),
        Text(
          'District: $district',
          style: Theme.of(context).textTheme.titleMedium,
        ),
      ],
    );
  }
}

class _AlertCard extends StatelessWidget {
  const _AlertCard({required this.alert});

  final PestAlert alert;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: <Widget>[
                Expanded(
                  child: Text(
                    '${alert.crop ?? 'General'} · ${alert.pest}',
                    style: theme.textTheme.titleMedium,
                  ),
                ),
                StatusBadge(status: alert.status),
              ],
            ),
            if (alert.category != null)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(
                  'Category: ${alert.category}',
                  style: theme.textTheme.bodySmall,
                ),
              ),
            if (alert.district != null)
              Padding(
                padding: const EdgeInsets.only(top: 2),
                child: Text(
                  'District: ${alert.district}',
                  style: theme.textTheme.bodySmall,
                ),
              ),
            if (alert.severity != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text('Severity: ${alert.severity}'),
              ),
            if (alert.reason != null)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(alert.reason!),
              ),
            if (alert.advisoryText != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(alert.advisoryText!),
              ),
            if (alert.pesticideName != null || alert.activeIngredient != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: _buildPesticideInfo(theme),
              ),
            if (alert.explicitDoseText != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: _InfoRow(
                  icon: Icons.scale,
                  label: 'Dose',
                  value: alert.explicitDoseText!,
                ),
              ),
            if (alert.safetyText != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: SafetyNotice(text: alert.safetyText!),
              ),
            if (alert.qualityControlStatus != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(
                  'Quality control: ${alert.qualityControlStatus}',
                  style: theme.textTheme.bodySmall,
                ),
              ),
            if (alert.sourceExcerpt != null && alert.sourceExcerpt!.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 12),
                child: _SourceCitation(
                  page: alert.sourcePage,
                  section: alert.sourceSection,
                  excerpt: alert.sourceExcerpt,
                ),
              ),
            if (alert.recommendations.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: alert.recommendations
                      .map((r) => _Bullet(text: r))
                      .toList(),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildPesticideInfo(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        if (alert.pesticideName != null)
          Text('Pesticide: ${alert.pesticideName}', style: theme.textTheme.bodyMedium),
        if (alert.activeIngredient != null)
          Text('Active ingredient: ${alert.activeIngredient}', style: theme.textTheme.bodyMedium),
        if (alert.formulation != null)
          Text('Formulation: ${alert.formulation}', style: theme.textTheme.bodyMedium),
      ],
    );
  }
}

class _AdvisoryCard extends StatelessWidget {
  const _AdvisoryCard({required this.advisory});

  final Advisory advisory;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: <Widget>[
                Expanded(
                  child: Text(
                    'Advisory: ${advisory.topic}',
                    style: theme.textTheme.titleMedium,
                  ),
                ),
                StatusBadge(status: advisory.status),
              ],
            ),
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Row(
                children: <Widget>[
                  Text(
                    'Source: ',
                    style: theme.textTheme.bodySmall,
                  ),
                  StatusBadge(status: advisory.sourceStatus),
                  if (advisory.matched)
                    Padding(
                      padding: const EdgeInsets.only(left: 8),
                      child: Chip(
                        label: const Text('MATCHED', style: TextStyle(fontSize: 10)),
                        backgroundColor: Colors.green.shade50,
                        side: BorderSide(color: Colors.green.shade300),
                        padding: EdgeInsets.zero,
                        labelPadding: const EdgeInsets.symmetric(horizontal: 6),
                      ),
                    ),
                ],
              ),
            ),
            if (advisory.reason != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(advisory.reason!),
              ),
            if (advisory.doseGuidance != null)
              Padding(
                padding: const EdgeInsets.only(top: 12),
                child: _InfoRow(
                  icon: Icons.scale,
                  label: 'Dose guidance',
                  value: advisory.doseGuidance!,
                ),
              ),
            if (advisory.safetyNotice != null)
              Padding(
                padding: const EdgeInsets.only(top: 12),
                child: SafetyNotice(text: advisory.safetyNotice!),
              ),
            if (advisory.recommendations.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: advisory.recommendations
                      .map((r) => _Bullet(text: r))
                      .toList(),
                ),
              ),
            if (advisory.citations.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: advisory.citations
                      .map((c) => _CitationTile(citation: c))
                      .toList(),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _SourcesSection extends StatelessWidget {
  const _SourcesSection({required this.sources});

  final List<PestSource> sources;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text('Data sources', style: theme.textTheme.titleMedium),
            const SizedBox(height: 8),
            ...sources.map((source) => _SourceTile(source: source)),
          ],
        ),
      ),
    );
  }
}

class _SourceTile extends StatelessWidget {
  const _SourceTile({required this.source});

  final PestSource source;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(source.title, style: theme.textTheme.bodyLarge),
          Text('Year: ${source.year}', style: theme.textTheme.bodySmall),
          Text('Status: ${source.status}', style: theme.textTheme.bodySmall),
          Text(
            'Pages: ${source.pageCount} · Facts: ${source.numFacts} · Review queue: ${source.numReviewQueue}',
            style: theme.textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}

class _CitationTile extends StatelessWidget {
  const _CitationTile({required this.citation});

  final PestCitation citation;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            'Citation: ${citation.factId} · ${citation.category}',
            style: theme.textTheme.bodySmall
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
          if (citation.sourceSection.isNotEmpty)
            Text(
              'Section: ${citation.sourceSection} · Page ${citation.sourcePage}',
              style: theme.textTheme.bodySmall,
            ),
          if (citation.sourceExcerpt.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(
                citation.sourceExcerpt,
                style: theme.textTheme.bodySmall?.copyWith(
                  fontStyle: FontStyle.italic,
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _SourceCitation extends StatelessWidget {
  const _SourceCitation({
    required this.page,
    required this.section,
    required this.excerpt,
  });

  final int page;
  final String? section;
  final String? excerpt;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          if (section != null)
            Text(
              'Source: $section · Page $page',
              style: theme.textTheme.bodySmall
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
          if (excerpt != null)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(
                excerpt!,
                style: theme.textTheme.bodySmall
                    ?.copyWith(fontStyle: FontStyle.italic),
              ),
            ),
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Icon(icon, size: 18, color: theme.colorScheme.primary),
        const SizedBox(width: 8),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(label, style: theme.textTheme.bodySmall),
              Text(value, style: theme.textTheme.bodyMedium),
            ],
          ),
        ),
      ],
    );
  }
}

class _Bullet extends StatelessWidget {
  const _Bullet({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Text('• ', style: TextStyle(fontWeight: FontWeight.bold)),
          Expanded(child: Text(text)),
        ],
      ),
    );
  }
}
