// The early access form posts here. One row per request in Azure Table Storage: the address and
// when it was left. The same Function as the sibling sites' waitlists.
const { TableClient } = require('@azure/data-tables');
const crypto = require('crypto');

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

module.exports = async function (context, req) {
  const email = String(req.body?.email ?? '').trim().toLowerCase();

  if (!EMAIL_RE.test(email) || email.length > 254) {
    context.res = { status: 400, jsonBody: { error: 'A valid email is required.' } };
    return;
  }

  try {
    const client = TableClient.fromConnectionString(
      process.env.WAITLIST_TABLE_CONNECTION_STRING,
      process.env.WAITLIST_TABLE_NAME || 'waitlist',
    );
    await client.createEntity({
      partitionKey: 'waitlist',
      rowKey: crypto.randomUUID(),
      email,
      submittedAt: new Date().toISOString(),
    });
    context.res = { status: 200, jsonBody: { ok: true } };
  } catch (err) {
    context.log.error('early access request failed', err);
    context.res = { status: 500, jsonBody: { error: 'Something went wrong. Please try again.' } };
  }
};
