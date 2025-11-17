// This file is not currently used but kept for potential future use
// The plugin focuses on the dashboard widget for barcode scanning

import {
  checkPluginVersion,
  type InvenTreePluginContext
} from '@inventreedb/ui';
import { Text } from '@mantine/core';

/**
 * Placeholder panel - not currently used.
 * The plugin provides stock removal functionality via dashboard widget.
 */
function ContinouousStockAdjustmentPanel() {
  return (
    <Text>
      Use the dashboard widget for continuous stock adjustment via barcode
      scanning.
    </Text>
  );
}

// This is the function which is called by InvenTree to render the actual panel component
export function renderContinouousStockAdjustmentPanel(
  context: InvenTreePluginContext
) {
  checkPluginVersion(context);
  return <ContinouousStockAdjustmentPanel />;
}
