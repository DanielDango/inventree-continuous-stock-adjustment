import type { InvenTreePluginContext } from '@inventreedb/ui';
import { Alert, Text } from '@mantine/core';

function PluginSettingsDisplay({
  context: _context
}: {
  context: InvenTreePluginContext;
}) {
  return (
    <Alert color='blue' title='Continuous Stock Adjustment'>
      <Text>
        This plugin provides barcode scanning for quick stock removal.
      </Text>
      <Text>
        Use the dashboard widget to scan barcodes and remove package quantities
        from stock.
      </Text>
    </Alert>
  );
}

export function renderPluginSettings(context: InvenTreePluginContext) {
  return <PluginSettingsDisplay context={context} />;
}
