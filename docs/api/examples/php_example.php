<?php
/**
 * DYGSOM Fraud API - PHP Integration Example
 *
 * Requirements: PHP 7.4+, cURL extension
 *
 * Usage:
 *   export DYGSOM_API_KEY=your_api_key_here
 *   php php_example.php
 */

class DYGSOMFraudClient {
    private $apiKey;
    private $baseURL = 'https://api.dygsom.com';
    private $timeout = 5;

    public function __construct($apiKey = null) {
        $this->apiKey = $apiKey ?: getenv('DYGSOM_API_KEY');

        if (!$this->apiKey) {
            throw new Exception('API key is required. Set DYGSOM_API_KEY environment variable.');
        }

        echo "Initialized DYGSOM client with base URL: {$this->baseURL}\n";
    }

    public function checkFraud($transaction) {
        echo "Checking fraud for transaction: {$transaction['transaction_id']}\n";

        $url = $this->baseURL . '/api/v1/fraud/score';

        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($transaction));
        curl_setopt($ch, CURLOPT_TIMEOUT, $this->timeout);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Content-Type: application/json',
            'X-API-Key: ' . $this->apiKey
        ]);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);

        if ($error) {
            throw new Exception('API request failed: ' . $error);
        }

        if ($httpCode === 401) {
            throw new Exception('Invalid API key. Check your credentials.');
        } elseif ($httpCode === 422) {
            throw new Exception('Validation error: ' . $response);
        } elseif ($httpCode === 429) {
            throw new Exception('Rate limit exceeded. Retry after 60 seconds.');
        } elseif ($httpCode !== 200) {
            throw new Exception('API error: HTTP ' . $httpCode);
        }

        $result = json_decode($response, true);
        echo "Fraud check complete: {$result['risk_level']} (score: {$result['fraud_score']})\n";

        return $result;
    }

    public function checkFraudWithRetry($transaction, $maxRetries = 3) {
        for ($attempt = 0; $attempt < $maxRetries; $attempt++) {
            try {
                return $this->checkFraud($transaction);
            } catch (Exception $e) {
                echo "Attempt " . ($attempt + 1) . "/$maxRetries failed: {$e->getMessage()}\n";

                if ($attempt < $maxRetries - 1) {
                    $waitTime = pow(2, $attempt);
                    echo "Retrying in $waitTime seconds...\n";
                    sleep($waitTime);
                    continue;
                }

                echo "All retry attempts failed. Returning safe default response.\n";
                return $this->getSafeDefault();
            }
        }
    }

    private function getSafeDefault() {
        return [
            'fraud_score' => 0.5,
            'risk_level' => 'MEDIUM',
            'recommendation' => 'REVIEW',
            'factors' => [
                'velocity_score' => 0.0,
                'amount_risk' => 0.0,
                'location_risk' => 0.0,
                'device_risk' => 0.0
            ],
            'processing_time_ms' => 0,
            'timestamp' => gmdate('Y-m-d\TH:i:s\Z'),
            'fallback' => true
        ];
    }
}

function processTransaction($transaction) {
    $client = new DYGSOMFraudClient();

    try {
        $result = $client->checkFraudWithRetry($transaction);
        $recommendation = $result['recommendation'];

        if ($recommendation === 'APPROVE') {
            echo "Transaction APPROVED - processing payment\n";
            return [
                'status' => 'approved',
                'transaction_id' => $transaction['transaction_id'],
                'fraud_score' => $result['fraud_score']
            ];
        } elseif ($recommendation === 'REVIEW') {
            echo "Transaction requires REVIEW - queuing for manual review\n";
            return [
                'status' => 'pending_review',
                'transaction_id' => $transaction['transaction_id'],
                'fraud_score' => $result['fraud_score']
            ];
        } elseif ($recommendation === 'REJECT') {
            echo "Transaction REJECTED - high fraud risk\n";
            return [
                'status' => 'declined',
                'transaction_id' => $transaction['transaction_id'],
                'fraud_score' => $result['fraud_score'],
                'reason' => 'fraud_detected'
            ];
        }
    } catch (Exception $e) {
        echo "Failed to process transaction: {$e->getMessage()}\n";
        return [
            'status' => 'error_review_required',
            'transaction_id' => $transaction['transaction_id'],
            'error' => $e->getMessage()
        ];
    }
}

function createExampleTransaction() {
    $timestampMs = round(microtime(true) * 1000);
    return [
        'transaction_id' => "tx-$timestampMs-EXAMPLE",
        'customer_email' => 'john.doe@example.com',
        'customer_ip' => '203.0.113.45',
        'amount' => 299.99,
        'currency' => 'USD',
        'merchant_id' => 'merchant-042',
        'card_bin' => '424242',
        'device_id' => 'device-xyz789',
        'timestamp' => gmdate('Y-m-d\TH:i:s\Z')
    ];
}

// Main execution
echo str_repeat('=', 60) . "\n";
echo "DYGSOM Fraud API - PHP Example\n";
echo str_repeat('=', 60) . "\n\n";

$transaction = createExampleTransaction();

echo "Transaction Details:\n";
echo "  ID: {$transaction['transaction_id']}\n";
echo "  Email: {$transaction['customer_email']}\n";
echo "  Amount: {$transaction['currency']} {$transaction['amount']}\n\n";

echo "Processing transaction...\n";
$result = processTransaction($transaction);

echo "\nResult:\n";
echo "  Status: {$result['status']}\n";
echo "  Fraud Score: " . ($result['fraud_score'] ?? 'N/A') . "\n\n";

echo str_repeat('=', 60) . "\n";
?>
