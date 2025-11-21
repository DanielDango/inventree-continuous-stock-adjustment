// Import for type checking
import {
  checkPluginVersion,
  type InvenTreePluginContext
} from '@inventreedb/ui';
import {
  Button,
  Group,
  Modal,
  Stack,
  Table,
  Text,
  TextInput,
  Title
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useCallback, useEffect, useRef, useState } from 'react';

interface ScanResult {
  success: boolean;
  message: string;
  part_id?: number;
  part_name?: string;
  quantity_removed?: number;
  remaining_stock?: number;
  confirmation_required?: boolean;
  quantity_to_remove?: number;
  timestamp: Date;
}

interface PendingConfirmation {
  barcode: string;
  partName: string;
  quantity: number;
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
  const [confirmationThreshold, setConfirmationThreshold] = useState<number>(2);
  const [defaultQuantity, setDefaultQuantity] = useState<number>(1);
  const [rescanTimeout, setRescanTimeout] = useState<number>(3);
  const [pendingConfirmation, setPendingConfirmation] =
    useState<PendingConfirmation | null>(null);
  const [lastScannedBarcode, setLastScannedBarcode] = useState<string | null>(
    null
  );
  const [lastScanTime, setLastScanTime] = useState<number>(0);
  const barcodeInputRef = useRef<HTMLInputElement>(null);

  // Fetch plugin settings on mount
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const response = await context.api.get(
          '/plugin/continouous-stock-adjustment/settings/'
        );
        if (response.data?.confirmation_threshold) {
          setConfirmationThreshold(response.data.confirmation_threshold);
        }
        if (response.data?.default_quantity) {
          setDefaultQuantity(response.data.default_quantity);
        }
        if (response.data?.rescan_timeout) {
          setRescanTimeout(response.data.rescan_timeout);
        }
      } catch (error) {
        console.error('Failed to fetch plugin settings:', error);
      }
    };

    fetchSettings();
  }, [context.api]);

  // Ensure the barcode input is focused when component mounts and when modal closes
  useEffect(() => {
    // Focus immediately on mount
    barcodeInputRef.current?.focus();

    // Smart refocus: only refocus if user clicks on non-interactive elements
    const handleDocumentClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement;

      // Don't refocus if modal is open or currently scanning
      if (pendingConfirmation || isScanning) {
        return;
      }

      // Check if the click target is an interactive element
      const isInteractive =
        target.tagName === 'INPUT' ||
        target.tagName === 'BUTTON' ||
        target.tagName === 'TEXTAREA' ||
        target.tagName === 'SELECT' ||
        target.tagName === 'A' ||
        target.closest('button') !== null ||
        target.closest('input') !== null ||
        target.closest('textarea') !== null ||
        target.closest('select') !== null ||
        target.closest('a') !== null ||
        target.closest('[role="button"]') !== null ||
        target.closest('[role="textbox"]') !== null ||
        target.closest('[contenteditable="true"]') !== null;

      // Only refocus if clicking on non-interactive elements
      if (!isInteractive) {
        barcodeInputRef.current?.focus();
      }
    };

    document.addEventListener('click', handleDocumentClick);

    return () => {
      document.removeEventListener('click', handleDocumentClick);
    };
  }, [pendingConfirmation, isScanning]);

  const performScan = useCallback(
    async (
      barcodeValue: string,
      confirmed: boolean = false,
      overrideQuantity?: number
    ) => {
      setIsScanning(true);

      try {
        const url = `/plugin/continouous-stock-adjustment/scan/`;
        const requestData: any = {
          barcode: barcodeValue.trim(),
          confirmed: confirmed
        };

        if (overrideQuantity !== undefined) {
          requestData.quantity = overrideQuantity;
        }

        const response = await context.api.post(url, requestData);

        const result: ScanResult = {
          ...response.data,
          timestamp: new Date()
        };

        const now = Date.now();
        const timeSinceLastScan = now - lastScanTime;
        const isSameBarcodeRecent =
          barcodeValue === lastScannedBarcode &&
          timeSinceLastScan < rescanTimeout * 1000;

        // Check if confirmation is required
        if (result.confirmation_required && !confirmed) {
          // If scanning the same barcode again within timeout window, use default quantity
          if (isSameBarcodeRecent) {
            // Re-scan detected, remove default quantity without confirmation
            setLastScanTime(now);
            await performScan(barcodeValue, true, defaultQuantity);
            return;
          }

          setPendingConfirmation({
            barcode: barcodeValue,
            partName: result.part_name || 'Unknown Part',
            quantity: result.quantity_to_remove || 0
          });
          setLastScannedBarcode(barcodeValue);
          setLastScanTime(now);
          setIsScanning(false);
          return;
        }

        setScanHistory((prev) => [result, ...prev.slice(0, 9)]);

        if (result.success) {
          notifications.show({
            title: 'Success',
            message: result.message,
            color: 'green'
          });
          setLastScannedBarcode(barcodeValue);
          setLastScanTime(now);
        } else {
          notifications.show({
            title: 'Error',
            message: result.message,
            color: 'red'
          });
          setLastScannedBarcode(null);
          setLastScanTime(0);
        }

        // Clear barcode input regardless of result
        setBarcode('');
        // Refocus input for continuous scanning
        setTimeout(() => barcodeInputRef.current?.focus(), 100);
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
        setLastScannedBarcode(null);
        setLastScanTime(0);

        // Clear barcode input even on exception
        setBarcode('');
      } finally {
        setIsScanning(false);
      }
    },
    [
      context.api,
      lastScannedBarcode,
      lastScanTime,
      defaultQuantity,
      rescanTimeout
    ]
  );

  const handleScan = useCallback(async () => {
    if (!barcode.trim()) {
      notifications.show({
        title: 'Error',
        message: 'Please enter a barcode',
        color: 'red'
      });
      return;
    }

    await performScan(barcode.trim(), false);
  }, [barcode, performScan]);

  const handleConfirm = useCallback(async () => {
    if (pendingConfirmation) {
      setPendingConfirmation(null);
      await performScan(pendingConfirmation.barcode, true);
      setBarcode('');
      // Refocus input after confirmation
      setTimeout(() => barcodeInputRef.current?.focus(), 100);
    }
  }, [pendingConfirmation, performScan]);

  const handleRemoveDefault = useCallback(async () => {
    if (pendingConfirmation) {
      setPendingConfirmation(null);
      await performScan(pendingConfirmation.barcode, true, defaultQuantity);
      setBarcode('');
      // Refocus input after default removal
      setTimeout(() => barcodeInputRef.current?.focus(), 100);
    }
  }, [pendingConfirmation, performScan, defaultQuantity]);

  const handleCancelConfirmation = useCallback(() => {
    setPendingConfirmation(null);
    setLastScannedBarcode(null);
    setLastScanTime(0);
    setBarcode('');
    notifications.show({
      title: 'Cancelled',
      message: 'Stock removal cancelled',
      color: 'yellow'
    });
    // Refocus input after cancellation
    setTimeout(() => barcodeInputRef.current?.focus(), 100);
  }, []);

  const handleKeyPress = useCallback(
    (event: React.KeyboardEvent<HTMLInputElement>) => {
      if (event.key === 'Enter' && !isScanning) {
        // If modal is open and user scans the same barcode, trigger default removal
        if (
          pendingConfirmation &&
          barcode.trim() === pendingConfirmation.barcode
        ) {
          event.preventDefault();
          handleRemoveDefault();
          return;
        }

        // Normal scan handling
        if (!pendingConfirmation) {
          handleScan();
        }
      }
    },
    [handleScan, isScanning, pendingConfirmation, barcode, handleRemoveDefault]
  );

  return (
    <Stack gap='md'>
      <Title order={4}>Quick Stock Removal</Title>
      <Text size='sm' c='dimmed'>
        Scan or enter a barcode to remove stock
      </Text>

      <TextInput
        ref={barcodeInputRef}
        label='Barcode'
        placeholder='Enter or scan barcode...'
        value={barcode}
        onChange={(e) => setBarcode(e.currentTarget.value)}
        onKeyPress={handleKeyPress}
        disabled={isScanning}
        autoFocus
        style={
          pendingConfirmation
            ? { visibility: 'hidden', position: 'absolute' }
            : undefined
        }
      />

      <Button
        onClick={handleScan}
        loading={isScanning}
        disabled={!barcode.trim()}
        style={pendingConfirmation ? { display: 'none' } : undefined}
      >
        Remove Stock
      </Button>

      {/* Confirmation Modal */}
      <Modal
        opened={pendingConfirmation !== null}
        onClose={handleCancelConfirmation}
        title='Confirm Large Quantity Removal'
        centered
      >
        <Stack gap='md'>
          <Text>
            You are about to remove{' '}
            <strong>{pendingConfirmation?.quantity}</strong> units of{' '}
            <strong>{pendingConfirmation?.partName}</strong>.
          </Text>
          <Text size='sm' c='dimmed'>
            This exceeds the confirmation threshold of {confirmationThreshold}{' '}
            units.
          </Text>
          <Text size='sm' c='blue'>
            Tip: Scan the same barcode again to quickly remove {defaultQuantity}{' '}
            unit(s).
          </Text>
          <Group justify='space-between' gap='sm'>
            <Button variant='default' onClick={handleCancelConfirmation}>
              Cancel
            </Button>
            <Group gap='sm'>
              <Button color='blue' onClick={handleRemoveDefault}>
                Remove {defaultQuantity} unit(s)
              </Button>
              <Button color='red' onClick={handleConfirm}>
                Remove {pendingConfirmation?.quantity} unit(s)
              </Button>
            </Group>
          </Group>
        </Stack>
      </Modal>

      {scanHistory.length > 0 && (
        <Stack gap='xs'>
          <Text size='sm' fw={500}>
            Recent Scans
          </Text>
          <Table>
            <thead>
              <tr>
                <th style={{ width: '50%' }}>Message</th>
                <th style={{ width: '25%' }}>Part</th>
                <th style={{ width: '25%' }}>Quantity Removed</th>
              </tr>
            </thead>
            <tbody>
              {scanHistory.map((result, index) => (
                <tr key={index}>
                  <td>
                    <Text size='xs' c={result.success ? 'green' : 'red'} fw={500}>
                      {result.success ? '✓ Success' : '✗ Failed'}
                    </Text>
                    <Text size='xs'>{result.message}</Text>
                  </td>
                  <td>
                    {result.part_name ? (
                      <Text size='xs' c='dimmed'>
                        {result.part_name}
                      </Text>
                    ) : (
                      <Text size='xs' c='dimmed'>
                        N/A
                      </Text>
                    )}
                  </td>
                  <td>
                    {result.quantity_removed !== undefined ? (
                      <Text size='xs' c='dimmed'>
                        {result.quantity_removed}
                      </Text>
                    ) : (
                      <Text size='xs' c='dimmed'>
                        N/A
                      </Text>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
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
