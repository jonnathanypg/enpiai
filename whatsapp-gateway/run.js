// PM2 entry point for the WhatsApp Gateway wrapper
// This strictly ensures that the environment is fully loaded BEFORE npx runs
require('dotenv').config({ path: require('path').resolve(__dirname, '.env') });
require('child_process').execSync('npx --yes @agenticnucleus/whatsapp-multitenant', { stdio: 'inherit' });
