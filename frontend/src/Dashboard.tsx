// Import for type checking
import {
  checkPluginVersion,
  type InvenTreePluginContext
} from '@inventreedb/ui';
import { Button, Stack, Text, Title } from '@mantine/core';

/**
 * Render a custom dashboard item with the provided context
 * Refer to the InvenTree documentation for the context interface
 * https://docs.inventree.org/en/stable/extend/plugins/ui/#plugin-context
 */
function ContinouousStockAdjustmentDashboardItem() {
  const stockRemovalUrl = '/app/plugin/continouous-stock-adjustment/stock-removal/';

  return (
    <Stack gap='md'>
      <Title order={4}>Quick Stock Removal</Title>
      <Text size='sm' c='dimmed'>
        Scan barcodes to quickly remove stock from inventory
      </Text>

      <Button component='a' href={stockRemovalUrl} fullWidth>
        Open Stock Removal
      </Button>
    </Stack>
  );
}

// This is the function which is called by InvenTree to render the actual dashboard
//  component
export function renderContinouousStockAdjustmentDashboardItem(
  context: InvenTreePluginContext
) {
  // Defensive check for context
  if (!context) {
    console.error('Dashboard: Context is null or undefined');
    return <Text c='red'>Error: Plugin context not provided</Text>;
  }

  checkPluginVersion(context);
  return <ContinouousStockAdjustmentDashboardItem />;
}
