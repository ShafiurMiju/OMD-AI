<script lang="ts">
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';

	export let plans = [];
	export let selectedPlanId = null;
	export let onSelectPlan = (planId: string) => {};

	const formatPrice = (price: number, currency: string = 'USD') => {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: currency
		}).format(price);
	};

	const getIntervalText = (interval: string) => {
		const intervalMap = {
			month: 'per month',
			year: 'per year',
			lifetime: 'one-time payment'
		};
		return intervalMap[interval] || interval;
	};

	const selectPlan = (planId: string) => {
		selectedPlanId = planId;
		onSelectPlan(planId);
	};
</script>

<div class="subscription-plans">
	<h2 class="text-2xl font-semibold mb-6 text-center">Choose Your Plan</h2>

	<div class="plans-grid grid grid-cols-1 md:grid-cols-3 gap-6">
		{#each plans as plan}
			<div
				class="plan-card relative rounded-lg border-2 p-6 transition-all hover:shadow-lg {selectedPlanId ===
				plan.id
					? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
					: 'border-gray-200 dark:border-gray-700'}"
			>
				{#if plan.name.toLowerCase().includes('popular') || plan.name.toLowerCase().includes('pro')}
					<div
						class="absolute top-0 right-0 bg-blue-500 text-white text-xs font-bold px-3 py-1 rounded-bl-lg rounded-tr-lg"
					>
						POPULAR
					</div>
				{/if}

				<div class="plan-header mb-4">
					<h3 class="text-xl font-bold mb-2">{plan.name}</h3>
					<div class="price mb-2">
						<span class="text-3xl font-bold">{formatPrice(plan.price, plan.currency)}</span>
						<span class="text-gray-500 dark:text-gray-400 text-sm ml-1">
							{getIntervalText(plan.interval)}
						</span>
					</div>
					{#if plan.description}
						<p class="text-gray-600 dark:text-gray-300 text-sm">{plan.description}</p>
					{/if}
				</div>

				<div class="plan-features mb-6">
					{#if plan.features}
						<ul class="space-y-2">
							{#if plan.features.maxChats}
								<li class="flex items-center text-sm">
									<svg
										class="w-4 h-4 mr-2 text-green-500"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M5 13l4 4L19 7"
										/>
									</svg>
									{plan.features.maxChats === -1
										? 'Unlimited chats'
										: `${plan.features.maxChats} chats`}
								</li>
							{/if}
							{#if plan.features.maxModels}
								<li class="flex items-center text-sm">
									<svg
										class="w-4 h-4 mr-2 text-green-500"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M5 13l4 4L19 7"
										/>
									</svg>
									{plan.features.maxModels === -1
										? 'All AI models'
										: `${plan.features.maxModels} AI models`}
								</li>
							{/if}
							{#if plan.features.prioritySupport}
								<li class="flex items-center text-sm">
									<svg
										class="w-4 h-4 mr-2 text-green-500"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M5 13l4 4L19 7"
										/>
									</svg>
									Priority support
								</li>
							{/if}
							{#if plan.features.customFeatures && Array.isArray(plan.features.customFeatures)}
								{#each plan.features.customFeatures as feature}
									<li class="flex items-center text-sm">
										<svg
											class="w-4 h-4 mr-2 text-green-500"
											fill="none"
											stroke="currentColor"
											viewBox="0 0 24 24"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M5 13l4 4L19 7"
											/>
										</svg>
										{feature}
									</li>
								{/each}
							{/if}
						</ul>
					{/if}
				</div>

				<button
					on:click={() => selectPlan(plan.id)}
					class="w-full py-2 px-4 rounded-lg font-semibold transition-all {selectedPlanId === plan.id
						? 'bg-blue-500 text-white hover:bg-blue-600'
						: 'bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600'}"
				>
					{selectedPlanId === plan.id ? 'Selected' : 'Select Plan'}
				</button>
			</div>
		{/each}
	</div>
</div>

<style>
	.subscription-plans {
		width: 100%;
		max-width: 1200px;
		margin: 0 auto;
	}

	.plans-grid {
		display: grid;
	}

	.plan-card {
		display: flex;
		flex-direction: column;
		background: var(--color-bg);
	}

	@media (max-width: 768px) {
		.plans-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
