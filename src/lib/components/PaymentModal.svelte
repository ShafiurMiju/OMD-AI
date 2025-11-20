<script lang="ts">
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';

	export let plan = null;
	export let amount = 0;
	export let onSuccess = (paymentId: string) => {};
	export let onCancel = () => {};

	let loading = false;
	let paymentMethod = 'stripe'; // stripe, paypal, etc.

	// Initialize payment gateway (Stripe example)
	const initializeStripe = async () => {
		// TODO: Replace with your actual Stripe publishable key
		// const stripe = Stripe('pk_test_YOUR_PUBLISHABLE_KEY');
		console.log('Stripe initialization - Add your publishable key here');
	};

	// Initialize PayPal
	const initializePayPal = async () => {
		// TODO: Add PayPal SDK initialization
		console.log('PayPal initialization - Add your client ID here');
	};

	const processStripePayment = async () => {
		loading = true;
		try {
			// TODO: Implement actual Stripe payment flow
			// 1. Create payment intent on backend
			// 2. Confirm payment with Stripe
			// 3. Return payment ID

			// Mock payment for demonstration
			await new Promise((resolve) => setTimeout(resolve, 2000));
			const mockPaymentId = 'pi_' + Math.random().toString(36).substring(7);

			toast.success('Payment successful!');
			onSuccess(mockPaymentId);
		} catch (error) {
			console.error('Payment error:', error);
			toast.error('Payment failed. Please try again.');
		} finally {
			loading = false;
		}
	};

	const processPayPalPayment = async () => {
		loading = true;
		try {
			// TODO: Implement actual PayPal payment flow
			// 1. Create order on backend
			// 2. Redirect to PayPal or show PayPal buttons
			// 3. Capture payment and return transaction ID

			// Mock payment for demonstration
			await new Promise((resolve) => setTimeout(resolve, 2000));
			const mockPaymentId = 'PAYPAL-' + Math.random().toString(36).substring(7);

			toast.success('Payment successful!');
			onSuccess(mockPaymentId);
		} catch (error) {
			console.error('Payment error:', error);
			toast.error('Payment failed. Please try again.');
		} finally {
			loading = false;
		}
	};

	const handlePayment = async () => {
		if (paymentMethod === 'stripe') {
			await processStripePayment();
		} else if (paymentMethod === 'paypal') {
			await processPayPalPayment();
		}
	};

	onMount(() => {
		if (paymentMethod === 'stripe') {
			initializeStripe();
		} else if (paymentMethod === 'paypal') {
			initializePayPal();
		}
	});
</script>

<div class="payment-modal">
	<div class="modal-content rounded-lg p-6 bg-white dark:bg-gray-800 max-w-md mx-auto">
		<h2 class="text-2xl font-bold mb-4">Complete Payment</h2>

		{#if plan}
			<div class="plan-summary mb-6 p-4 bg-gray-100 dark:bg-gray-700 rounded-lg">
				<h3 class="font-semibold mb-2">{plan.name}</h3>
				<p class="text-sm text-gray-600 dark:text-gray-300 mb-2">{plan.description}</p>
				<div class="text-2xl font-bold">
					${amount.toFixed(2)}
					<span class="text-sm font-normal text-gray-500">
						{plan.interval === 'month' ? '/ month' : plan.interval === 'year' ? '/ year' : ''}
					</span>
				</div>
			</div>
		{/if}

		<div class="payment-methods mb-6">
			<label class="block text-sm font-medium mb-2">Payment Method</label>
			<div class="space-y-2">
				<label class="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 {paymentMethod === 'stripe' ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-300 dark:border-gray-600'}">
					<input
						type="radio"
						name="payment-method"
						value="stripe"
						bind:group={paymentMethod}
						class="mr-3"
					/>
					<svg class="w-6 h-6 mr-2" viewBox="0 0 24 24" fill="none">
						<rect width="24" height="24" rx="4" fill="#635BFF" />
						<path
							d="M10.5 10.5c0-.9.7-1.5 1.8-1.5 1.6 0 3.6.5 5.2 1.4V7.3c-1.7-.6-3.3-.9-5.2-.9-4.2 0-7 2.2-7 5.9 0 5.7 7.9 4.8 7.9 7.3 0 1-.8 1.6-2 1.6-1.7 0-3.9-.7-5.6-1.7v3.2c1.9.8 3.8 1.2 5.6 1.2 4.3 0 7.3-2.1 7.3-5.9 0-6.2-8-5.1-8-7.5z"
							fill="white"
						/>
					</svg>
					<span>Credit Card (Stripe)</span>
				</label>

				<label class="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 {paymentMethod === 'paypal' ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-300 dark:border-gray-600'}">
					<input
						type="radio"
						name="payment-method"
						value="paypal"
						bind:group={paymentMethod}
						class="mr-3"
					/>
					<svg class="w-6 h-6 mr-2" viewBox="0 0 24 24">
						<path
							fill="#003087"
							d="M20.905 9.5c.2-1.3.1-2.2-.4-2.9-.6-.9-1.8-1.3-3.4-1.3h-6.3c-.4 0-.8.3-.9.7l-2.6 16.5c-.1.3.2.6.5.6h3.8l1-6.1v.2c.1-.4.5-.7.9-.7h1.9c3.7 0 6.6-1.5 7.5-5.8 0-.1 0-.2.1-.2-.1 0-.1 0-.1 0z"
						/>
						<path
							fill="#0070E0"
							d="M9.6 9.5c.1-.4.5-.7.9-.7h5.7c.7 0 1.3.1 1.8.2.1 0 .3.1.4.1.1 0 .2.1.3.1.2.1.4.1.5.2.2-1.3.1-2.2-.4-2.9-.6-.9-1.8-1.3-3.4-1.3h-6.3c-.4 0-.8.3-.9.7L4.6 21.4c-.1.3.2.6.5.6H8.9l2.6-16.5.1-.1z"
						/>
					</svg>
					<span>PayPal</span>
				</label>
			</div>
		</div>

		<div class="alert mb-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
			<p class="text-sm text-yellow-800 dark:text-yellow-200">
				<strong>Note:</strong> This is a demo payment interface. Integrate with actual payment gateway
				(Stripe, PayPal, etc.) for production use.
			</p>
		</div>

		<div class="actions flex gap-3">
			<button
				on:click={onCancel}
				disabled={loading}
				class="flex-1 py-2 px-4 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
			>
				Cancel
			</button>
			<button
				on:click={handlePayment}
				disabled={loading}
				class="flex-1 py-2 px-4 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 flex items-center justify-center"
			>
				{#if loading}
					<svg class="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
						<circle
							class="opacity-25"
							cx="12"
							cy="12"
							r="10"
							stroke="currentColor"
							stroke-width="4"
							fill="none"
						/>
						<path
							class="opacity-75"
							fill="currentColor"
							d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
						/>
					</svg>
					Processing...
				{:else}
					Pay ${amount.toFixed(2)}
				{/if}
			</button>
		</div>
	</div>
</div>

<style>
	.payment-modal {
		width: 100%;
	}

	.modal-content {
		box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
	}
</style>
