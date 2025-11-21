// Standalone page component for Stock Removal
// Accessible via navigation menu

import {
  checkPluginVersion,
  type InvenTreePluginContext
} from '@inventreedb/ui';
import {
  Button,
  Container,
  Paper,
  Stack,
  Text,
  TextInput,
  Title
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useCallback, useState } from 'react';

/**
 * Format a number to 2 decimal places
 * Removes .00 suffix for whole numbers
 * Handles both number and string inputs
 */
function formatNumber(value: any): string {
  if (value === undefined || value === null) {
    return 'N/A';
  }

  // Convert string to number if needed
  const numValue = typeof value === 'string' ? parseFloat(value) : value;

  // Check if it's a valid number
  if (typeof numValue !== 'number' || isNaN(numValue)) {
    return 'N/A';
  }

  const formatted = numValue.toFixed(2);
  return formatted.endsWith('.00') ? formatted.slice(0, -3) : formatted;
}

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
 * Standalone page component for continuous stock adjustment
 */
function StockRemovalPage({ context }: { context: InvenTreePluginContext }) {
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

  return (
    <Container size='md' py='xl'>
      <Stack gap='lg'>
        <div>
          <Title order={2}>Quick Stock Removal</Title>
          <Text size='sm' c='dimmed' mt='xs'>
            Scan or enter a barcode to quickly remove stock from inventory. The
            system will automatically detect the part and remove the appropriate
            quantity based on supplier package information.
          </Text>
        </div>

        <Paper shadow='sm' p='md' withBorder>
          <Stack gap='md'>
            <TextInput
              label='Barcode'
              placeholder='Enter or scan barcode...'
              value={barcode}
              onChange={(e) => setBarcode(e.currentTarget.value)}
              onKeyPress={handleKeyPress}
              disabled={isScanning}
              autoFocus
              size='lg'
            />

            <Button
              onClick={handleScan}
              loading={isScanning}
              disabled={!barcode.trim()}
              size='lg'
              fullWidth
            >
              Remove Stock
            </Button>
          </Stack>
        </Paper>

        {scanHistory.length > 0 && (
          <div>
            <Title order={4} mb='md'>
              Recent Scans
            </Title>
            <Stack gap='sm'>
              {scanHistory.map((result, index) => (
                <Paper key={index} p='md' withBorder shadow='xs'>
                  <Stack gap='xs'>
                    <Text
                      size='sm'
                      c={result.success ? 'green' : 'red'}
                      fw={600}
                    >
                      {result.success ? '✓ Success' : '✗ Failed'}
                    </Text>
                    <Text size='sm'>{result.message}</Text>
                    {result.part_name && (
                      <Text size='sm' c='dimmed'>
                        Part: {result.part_name}
                      </Text>
                    )}
                    {result.quantity_removed !== undefined && (
                      <Text size='sm' c='dimmed'>
                        Removed: {formatNumber(result.quantity_removed)} | Remaining:{' '}
                        {formatNumber(result.remaining_stock)}
                      </Text>
                    )}
                    <Text size='xs' c='dimmed'>
                      {result.timestamp.toLocaleTimeString()}
                    </Text>
                  </Stack>
                </Paper>
              ))}
            </Stack>
          </div>
        )}
      </Stack>
    </Container>
  );
}

// This is the function which is called by InvenTree to render the page
export function renderStockRemovalPage(context: InvenTreePluginContext) {
  // Defensive check for context
  if (!context) {
    console.error('StockRemovalPage: Context is null or undefined');
    return <Text c='red'>Error: Plugin context not provided</Text>;
  }

  checkPluginVersion(context);
  return <StockRemovalPage context={context} />;
}
