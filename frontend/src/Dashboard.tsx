// Import for type checking
import {
  checkPluginVersion,
  type InvenTreePluginContext
} from '@inventreedb/ui';
import { Anchor, Button, Paper, Stack, Text, TextInput, Title } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useCallback, useState } from 'react';

interface ScanResult {
  success: boolean;
  message: string;
  part_id?: number;
  part_name?: string;
  quantity_removed?: number;
  remaining_stock?: number;
  timestamp: Date;
}

/**
 * Render a custom dashboard item with the provided context
 * Refer to the InvenTree documentation for the context interface
 * https://docs.inventree.org/en/stable/extend/plugins/ui/#plugin-context
 */
function ContinouousStockAdjustmentDashboardItem({
  context
}: {
  context: InvenTreePluginContext;
}) {
  const [barcode, setBarcode] = useState<string>('');
  const [scanHistory, setScanHistory] = useState<ScanResult[]>([]);
  const [isScanning, setIsScanning] = useState<boolean>(false);

  const handleScan = useCallback(async () => {
    if (!barcode.trim()) {
      notifications.show({
        title: 'Error',
        message: 'Please enter a barcode',
        color: 'red'
      });
      return;
    }

    setIsScanning(true);

    try {
      const url = `/plugin/continouous-stock-adjustment/scan/`;
      const response = await context.api.post(url, {
        barcode: barcode.trim()
      });

      const result: ScanResult = {
        ...response.data,
        timestamp: new Date()
      };

      setScanHistory((prev) => [result, ...prev.slice(0, 9)]);

      if (result.success) {
        notifications.show({
          title: 'Success',
          message: result.message,
          color: 'green'
        });
        setBarcode('');
      } else {
        notifications.show({
          title: 'Error',
          message: result.message,
          color: 'red'
        });
      }
    } catch (error: any) {
      const errorMessage =
        error?.response?.data?.message || 'Failed to process barcode';
      notifications.show({
        title: 'Error',
        message: errorMessage,
        color: 'red'
      });

      setScanHistory((prev) => [
        {
          success: false,
          message: errorMessage,
          timestamp: new Date()
        },
        ...prev.slice(0, 9)
      ]);
    } finally {
      setIsScanning(false);
    }
  }, [barcode, context.api]);

  const handleKeyPress = useCallback(
    (event: React.KeyboardEvent<HTMLInputElement>) => {
      if (event.key === 'Enter' && !isScanning) {
        handleScan();
      }
    },
    [handleScan, isScanning]
  );

  const stockRemovalUrl = '/app/plugin/continouous-stock-adjustment/stock-removal/';

  return (
    <Stack gap='md'>
      <Title order={4}>
        <Anchor href={stockRemovalUrl} underline='hover'>
          Quick Stock Removal
        </Anchor>
      </Title>
      <Text size='sm' c='dimmed'>
        Scan or enter a barcode to remove stock
      </Text>

      <TextInput
        label='Barcode'
        placeholder='Enter or scan barcode...'
        value={barcode}
        onChange={(e) => setBarcode(e.currentTarget.value)}
        onKeyPress={handleKeyPress}
        disabled={isScanning}
        autoFocus
      />

      <Button
        onClick={handleScan}
        loading={isScanning}
        disabled={!barcode.trim()}
      >
        Remove Stock
      </Button>

      {scanHistory.length > 0 && (
        <Stack gap='xs'>
          <Text size='sm' fw={500}>
            Recent Scans
          </Text>
          {scanHistory.map((result, index) => (
            <Paper key={index} p='xs' withBorder>
              <Stack gap='xs'>
                <Text size='xs' c={result.success ? 'green' : 'red'} fw={500}>
                  {result.success ? '✓ Success' : '✗ Failed'}
                </Text>
                <Text size='xs'>{result.message}</Text>
                {result.part_name && (
                  <Text size='xs' c='dimmed'>
                    Part: {result.part_name}
                  </Text>
                )}
                {result.quantity_removed !== undefined && (
                  <Text size='xs' c='dimmed'>
                    Removed: {result.quantity_removed} | Remaining:{' '}
                    {result.remaining_stock}
                  </Text>
                )}
                <Text size='xs' c='dimmed'>
                  {result.timestamp.toLocaleTimeString()}
                </Text>
              </Stack>
            </Paper>
          ))}
        </Stack>
      )}
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
  return <ContinouousStockAdjustmentDashboardItem context={context} />;
}
