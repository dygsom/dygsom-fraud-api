/**
 * DYGSOM Fraud API - Node.js Integration Example
 *
 * This example demonstrates how to integrate the DYGSOM Fraud Detection API
 * into a Node.js application with proper error handling and best practices.
 *
 * Requirements:
 *   npm install axios dotenv
 *
 * Usage:
 *   export DYGSOM_API_KEY=your_api_key_here
 *   node nodejs_example.js
 */

const axios = require('axios');
require('dotenv').config();

/**
 * DYGSOM Fraud Detection API Client
 */
class DYGSOMFraudClient {
  /**
   * Initialize the fraud client
   * @param {string|null} apiKey - API key (defaults to env var)
   * @param {string} baseURL - API base URL
   */
  constructor(apiKey = null, baseURL = 'https://api.dygsom.com') {
    this.apiKey = apiKey || process.env.DYGSOM_API_KEY;
    this.baseURL = baseURL;
    this.timeout = 5000; // milliseconds

    if (!this.apiKey) {
      throw new Error('API key is required. Set DYGSOM_API_KEY environment variable.');
    }

    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: this.timeout,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey
      }
    });

    console.log(`Initialized DYGSOM client with base URL: ${this.baseURL}`);
  }

  /**
   * Check a transaction for fraud
   * @param {Object} transaction - Transaction data
   * @returns {Promise<Object>} Fraud assessment result
   */
  async checkFraud(transaction) {
    console.log(`Checking fraud for transaction: ${transaction.transaction_id}`);

    try {
      const response = await this.client.post('/api/v1/fraud/score', transaction);
      const result = response.data;

      console.log(`Fraud check complete: ${result.risk_level} (score: ${result.fraud_score})`);

      return result;

    } catch (error) {
      if (error.code === 'ECONNABORTED') {
        console.error('API request timed out');
        throw new Error('Request timeout');
      }

      if (error.response) {
        const status = error.response.status;
        console.error(`API returned error: ${status}`);

        if (status === 401) {
          throw new Error('Invalid API key. Check your credentials.');
        } else if (status === 422) {
          throw new Error(`Validation error: ${JSON.stringify(error.response.data)}`);
        } else if (status === 429) {
          throw new Error('Rate limit exceeded. Retry after 60 seconds.');
        }
      }

      console.error(`Network error: ${error.message}`);
      throw error;
    }
  }

  /**
   * Check fraud with automatic retry logic
   * @param {Object} transaction - Transaction data
   * @param {number} maxRetries - Maximum retry attempts
   * @returns {Promise<Object>} Fraud assessment or safe default
   */
  async checkFraudWithRetry(transaction, maxRetries = 3) {
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        return await this.checkFraud(transaction);

      } catch (error) {
        console.warn(`Attempt ${attempt + 1}/${maxRetries} failed: ${error.message}`);

        if (attempt < maxRetries - 1) {
          const waitTime = Math.pow(2, attempt) * 1000; // Exponential backoff
          console.log(`Retrying in ${waitTime/1000} seconds...`);
          await this.sleep(waitTime);
          continue;
        }

        console.warn('All retry attempts failed. Returning safe default response.');
        return this.getSafeDefault();
      }
    }
  }

  /**
   * Get safe default response when API is unavailable
   * @returns {Object} Safe default fraud assessment
   */
  getSafeDefault() {
    return {
      fraud_score: 0.5,
      risk_level: 'MEDIUM',
      recommendation: 'REVIEW',
      factors: {
        velocity_score: 0.0,
        amount_risk: 0.0,
        location_risk: 0.0,
        device_risk: 0.0
      },
      processing_time_ms: 0,
      timestamp: new Date().toISOString(),
      fallback: true
    };
  }

  /**
   * Sleep utility for retry delays
   * @param {number} ms - Milliseconds to sleep
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

/**
 * Process a transaction based on fraud assessment
 * @param {Object} transaction - Transaction data
 * @returns {Promise<Object>} Processing result
 */
async function processTransaction(transaction) {
  const client = new DYGSOMFraudClient();

  try {
    const result = await client.checkFraudWithRetry(transaction);
    const recommendation = result.recommendation;

    if (recommendation === 'APPROVE') {
      console.log('Transaction APPROVED - processing payment');
      return {
        status: 'approved',
        transaction_id: transaction.transaction_id,
        fraud_score: result.fraud_score
      };

    } else if (recommendation === 'REVIEW') {
      console.warn('Transaction requires REVIEW - queuing for manual review');
      return {
        status: 'pending_review',
        transaction_id: transaction.transaction_id,
        fraud_score: result.fraud_score
      };

    } else if (recommendation === 'REJECT') {
      console.error('Transaction REJECTED - high fraud risk');
      return {
        status: 'declined',
        transaction_id: transaction.transaction_id,
        fraud_score: result.fraud_score,
        reason: 'fraud_detected'
      };
    }

  } catch (error) {
    console.error(`Failed to process transaction: ${error.message}`);
    return {
      status: 'error_review_required',
      transaction_id: transaction.transaction_id,
      error: error.message
    };
  }
}

/**
 * Create an example transaction for testing
 * @returns {Object} Example transaction
 */
function createExampleTransaction() {
  const timestampMs = Date.now();
  return {
    transaction_id: `tx-${timestampMs}-EXAMPLE`,
    customer_email: 'john.doe@example.com',
    customer_ip: '203.0.113.45',
    amount: 299.99,
    currency: 'USD',
    merchant_id: 'merchant-042',
    card_bin: '424242',
    device_id: 'device-xyz789',
    timestamp: new Date().toISOString()
  };
}

/**
 * Main execution function
 */
async function main() {
  console.log('='.repeat(60));
  console.log('DYGSOM Fraud API - Node.js Example');
  console.log('='.repeat(60));
  console.log();

  const transaction = createExampleTransaction();

  console.log('Transaction Details:');
  console.log(`  ID: ${transaction.transaction_id}`);
  console.log(`  Email: ${transaction.customer_email}`);
  console.log(`  Amount: ${transaction.currency} ${transaction.amount}`);
  console.log();

  console.log('Processing transaction...');
  const result = await processTransaction(transaction);

  console.log();
  console.log('Result:');
  console.log(`  Status: ${result.status}`);
  console.log(`  Fraud Score: ${result.fraud_score || 'N/A'}`);
  console.log();

  console.log('='.repeat(60));
}

// Run main function
if (require.main === module) {
  main().catch(error => {
    console.error('Error:', error.message);
    process.exit(1);
  });
}

// Export for use as module
module.exports = { DYGSOMFraudClient, processTransaction };
