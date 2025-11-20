<script>
	import { toast } from 'svelte-sonner';
	import dayjs from 'dayjs';
	import relativeTime from 'dayjs/plugin/relativeTime';
	dayjs.extend(relativeTime);

	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';

	import { config, user } from '$lib/stores';

	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Plus from '$lib/components/icons/Plus.svelte';
	import Search from '$lib/components/icons/Search.svelte';
	import CreditCard from '$lib/components/icons/CreditCard.svelte';
	import Pencil from '$lib/components/icons/Pencil.svelte';
	import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
	import EditPlanModal from './Plans/EditPlanModal.svelte';

	import {
		getSubscriptionPlans,
		createPlan,
		updatePlan,
		deletePlan
	} from '$lib/apis/subscriptions';

	const i18n = getContext('i18n');

	let loaded = false;
	let plans = [];
	let filteredPlans;

	$: filteredPlans = plans.filter((plan) => {
		if (search === '') {
			return true;
		} else {
			let name = plan.plan_name.toLowerCase();
			const query = search.toLowerCase();
			return name.includes(query);
		}
	});

	let search = '';
	let showAddPlanModal = false;
	let showEditPlanModal = false;
	let selectedPlan = null;

	const setPlans = async () => {
		try {
			const res = await getSubscriptionPlans(localStorage.token);
			if (res) {
				plans = res.map(plan => ({
					...plan,
					// Map backend fields to frontend fields
					active: plan.is_active
				}));
			}
		} catch (error) {
			toast.error(`${error}`);
			console.error('Error fetching plans:', error);
		}
	};

	const addPlanHandler = async (planData) => {
		try {
			console.log('Creating plan with data:', planData);
			console.log('Models selected:', planData.models);
			const res = await createPlan(localStorage.token, planData);
			if (res) {
				console.log('Plan created:', res);
				toast.success($i18n.t('Plan created successfully'));
				await setPlans();
			}
		} catch (error) {
			toast.error(`${error}`);
			console.error('Error creating plan:', error);
		}
	};

	const updatePlanHandler = async (planData) => {
		if (!selectedPlan) return;
		
		try {
			const res = await updatePlan(localStorage.token, selectedPlan.id, planData);
			if (res) {
				toast.success($i18n.t('Plan updated successfully'));
				await setPlans();
				selectedPlan = null;
			}
		} catch (error) {
			toast.error(`${error}`);
			console.error('Error updating plan:', error);
		}
	};

	const deletePlanHandler = async (planId) => {
		if (!confirm($i18n.t('Are you sure you want to delete this plan?'))) {
			return;
		}

		try {
			const res = await deletePlan(localStorage.token, planId);
			if (res) {
				toast.success($i18n.t('Plan deleted successfully'));
				await setPlans();
			}
		} catch (error) {
			toast.error(`${error}`);
			console.error('Error deleting plan:', error);
		}
	};

	const editPlanHandler = (plan) => {
		selectedPlan = plan;
		showEditPlanModal = true;
	};

	onMount(async () => {
		if ($user?.role !== 'admin') {
			await goto('/');
			return;
		}

		await setPlans();
		loaded = true;
	});
</script>

{#if loaded}
	<!-- Add Plan Modal -->
	<EditPlanModal
		bind:show={showAddPlanModal}
		edit={false}
		onSubmit={addPlanHandler}
	/>

	<!-- Edit Plan Modal -->
	<EditPlanModal
		bind:show={showEditPlanModal}
		edit={true}
		plan={selectedPlan}
		onSubmit={updatePlanHandler}
	/>

	<div class="mt-0.5 mb-2 gap-1 flex flex-col md:flex-row justify-between">
		<div class="flex md:self-center text-lg font-medium px-0.5">
			{$i18n.t('Plans')}
			<div class="flex self-center w-[1px] h-6 mx-2.5 bg-gray-50 dark:bg-gray-850" />

			<span class="text-lg font-medium text-gray-500 dark:text-gray-300">{plans.length}</span>
		</div>

		<div class="flex gap-1">
			<div class=" flex w-full space-x-2">
				<div class="flex flex-1">
					<div class=" self-center ml-1 mr-3">
						<Search />
					</div>
					<input
						class=" w-full text-sm pr-4 py-1 rounded-r-xl outline-hidden bg-transparent"
						bind:value={search}
						placeholder={$i18n.t('Search Plans')}
					/>
				</div>

				<div>
					<Tooltip content={$i18n.t('Create Plan')}>
						<button
							class=" p-2 rounded-xl hover:bg-gray-100 dark:bg-gray-900 dark:hover:bg-gray-850 transition font-medium text-sm flex items-center space-x-1"
							on:click={() => {
								showAddPlanModal = true;
							}}
						>
							<Plus className="size-3.5" />
						</button>
					</Tooltip>
				</div>
			</div>
		</div>
	</div>

	<div>
		{#if filteredPlans.length === 0}
			<div class="flex flex-col items-center justify-center h-40">
				<div class=" text-xl font-medium">
					{$i18n.t('Manage subscription plans')}
				</div>

				<div class="mt-1 text-sm dark:text-gray-300">
					{$i18n.t('Create and manage subscription plans for your users.')}
				</div>

				<div class="mt-3">
					<button
						class=" px-4 py-1.5 text-sm rounded-full bg-black hover:bg-gray-800 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition font-medium flex items-center space-x-1"
						aria-label={$i18n.t('Create Plan')}
						on:click={() => {
							showAddPlanModal = true;
						}}
					>
						{$i18n.t('Create Plan')}
					</button>
				</div>
			</div>
		{:else}
			<div>
				<div class=" flex items-center gap-3 justify-between text-xs uppercase px-1 font-semibold">
					<div class="w-full basis-2/5">{$i18n.t('Plan Name')}</div>
					<div class="w-full basis-1/5 text-center">{$i18n.t('Type')}</div>
					<div class="w-full basis-1/5 text-center">{$i18n.t('Price')}</div>
					<div class="w-full basis-1/5 text-center">{$i18n.t('Duration')}</div>
					<div class="w-16 text-right">{$i18n.t('Actions')}</div>
				</div>

				<hr class="mt-1.5 border-gray-100 dark:border-gray-850" />

				{#each filteredPlans as plan}
					<div class="my-2">
						<div
							class="flex items-center justify-between rounded-lg w-full transition hover:bg-gray-50 dark:hover:bg-gray-850 p-2"
						>
							<div class="w-full basis-2/5 flex items-center gap-2.5">
								<div class="p-1.5 bg-black/5 dark:bg-white/10 rounded-full">
									<CreditCard className="size-4" />
								</div>
								<div class="flex-1 min-w-0">
									<div class="text-sm font-medium truncate">{plan.plan_name}</div>
									<div class="text-xs text-gray-500 dark:text-gray-400 truncate">
										{#if plan.subtitle}
											{plan.subtitle}
										{:else if plan.benefits && plan.benefits.length > 0}
											{plan.benefits[0]}
										{/if}
									</div>
								</div>
							</div>

							<div class="w-full basis-1/5 text-center">
								<span class="px-2 py-1 text-xs font-medium rounded-full capitalize
									{plan.plan_type === 'free' ? 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200' : ''}
									{plan.plan_type === 'premium' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' : ''}
									{plan.plan_type === 'enterprise' ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200' : ''}
								">
									{plan.plan_type}
								</span>
							</div>

							<div class="w-full basis-1/5 text-center text-sm font-medium">
								{#if plan.price === 0}
									{$i18n.t('Free')}
								{:else}
									${plan.price}
								{/if}
							</div>

							<div class="w-full basis-1/5 text-center text-sm">
								{plan.plan_duration} {plan.duration_type}
							</div>

							<div class="w-16 flex items-center justify-end gap-1">
								<Tooltip content={$i18n.t('Edit')}>
									<button
										class="p-1.5 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-800 transition"
										on:click={() => editPlanHandler(plan)}
									>
										<Pencil className="size-3.5" />
									</button>
								</Tooltip>

								<Tooltip content={$i18n.t('Delete')}>
									<button
										class="p-1.5 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400 transition"
										on:click={() => deletePlanHandler(plan.id)}
									>
										<GarbageBin className="size-3.5" />
									</button>
								</Tooltip>
							</div>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
{/if}
