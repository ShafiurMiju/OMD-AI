<script>
	import { toast } from 'svelte-sonner';
	import dayjs from 'dayjs';
	import relativeTime from 'dayjs/plugin/relativeTime';
	dayjs.extend(relativeTime);

	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';

	import { user } from '$lib/stores';

	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Plus from '$lib/components/icons/Plus.svelte';
	import Search from '$lib/components/icons/Search.svelte';
	import OrganizationItem from './Organizations/OrganizationItem.svelte';
	import EditOrganizationModal from './Organizations/EditOrganizationModal.svelte';
	import {
		createNewOrganization,
		getOrganizations,
		updateOrganizationById,
		deleteOrganizationById
	} from '$lib/apis/organizations';
	import { getSubscriptionPlans } from '$lib/apis/subscriptions';

	const i18n = getContext('i18n');

	let loaded = false;

	let plans = [];
	let organizations = [];
	let filteredOrganizations;

	$: filteredOrganizations = organizations.filter((org) => {
		if (search === '') {
			return true;
		} else {
			let name = org.org_name.toLowerCase();
			let code = org.org_code.toLowerCase();
			const query = search.toLowerCase();
			return name.includes(query) || code.includes(query);
		}
	});

	let search = '';
	let showAddOrganizationModal = false;
	let showEditOrganizationModal = false;
	let selectedOrganization = null;

	const setOrganizations = async () => {
		organizations = await getOrganizations(localStorage.token);
	};

	const addOrganizationHandler = async (organization) => {
		const res = await createNewOrganization(localStorage.token, organization).catch((error) => {
			toast.error(`${error}`);
			return null;
		});

		if (res) {
			toast.success($i18n.t('Organization created successfully'));
			await setOrganizations();
		}
	};

	const updateOrganizationHandler = async (id, organization) => {
		const res = await updateOrganizationById(localStorage.token, id, organization).catch(
			(error) => {
				toast.error(`${error}`);
				return null;
			}
		);

		if (res) {
			toast.success($i18n.t('Organization updated successfully'));
			await setOrganizations();
		}
	};

	const deleteOrganizationHandler = async (id) => {
		const res = await deleteOrganizationById(localStorage.token, id).catch((error) => {
			toast.error(`${error}`);
			return null;
		});

		if (res) {
			toast.success($i18n.t('Organization deleted successfully'));
			await setOrganizations();
		}
	};

	onMount(async () => {
		if ($user?.role !== 'admin') {
			await goto('/');
			return;
		}

		const resPlans = await getSubscriptionPlans(localStorage.token).catch((error) => {
			toast.error(`${error}`);
			return null;
		});

		if (resPlans) {
			plans = resPlans;
		}

		await setOrganizations();
		loaded = true;
	});
</script>

{#if loaded}
	<EditOrganizationModal
		bind:show={showAddOrganizationModal}
		edit={false}
		{plans}
		onSubmit={addOrganizationHandler}
	/>

	{#if selectedOrganization}
		<EditOrganizationModal
			bind:show={showEditOrganizationModal}
			edit={true}
			organization={selectedOrganization}
			{plans}
			onSubmit={(data) => updateOrganizationHandler(selectedOrganization.id, data)}
		/>
	{/if}

	<div class="mt-0.5 mb-2 gap-1 flex flex-col md:flex-row justify-between">
		<div class="flex md:self-center text-lg font-medium px-0.5">
			{$i18n.t('Organizations')}
			<div class="flex self-center w-[1px] h-6 mx-2.5 bg-gray-50 dark:bg-gray-850" />

			<span class="text-lg font-medium text-gray-500 dark:text-gray-300"
				>{organizations.length}</span
			>
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
						placeholder={$i18n.t('Search')}
					/>
				</div>

				<div>
					<Tooltip content={$i18n.t('Create Organization')}>
						<button
							class=" p-2 rounded-xl hover:bg-gray-100 dark:bg-gray-900 dark:hover:bg-gray-850 transition font-medium text-sm flex items-center space-x-1"
							on:click={() => {
								showAddOrganizationModal = !showAddOrganizationModal;
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
		{#if filteredOrganizations.length === 0}
			<div class="flex flex-col items-center justify-center h-40">
				<div class=" text-xl font-medium">
					{$i18n.t('Manage your organizations')}
				</div>

				<div class="mt-1 text-sm dark:text-gray-300">
					{$i18n.t('Create organizations to group users and assign subscription plans.')}
				</div>

				<div class="mt-3">
					<button
						class=" px-4 py-1.5 text-sm rounded-full bg-black hover:bg-gray-800 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition font-medium flex items-center space-x-1"
						aria-label={$i18n.t('Create Organization')}
						on:click={() => {
							showAddOrganizationModal = true;
						}}
					>
						{$i18n.t('Create Organization')}
					</button>
				</div>
			</div>
		{:else}
			<div>
				<div
					class=" flex items-center gap-3 justify-between text-xs uppercase px-1 font-semibold"
				>
					<div class="w-full basis-2/5">{$i18n.t('Organization')}</div>
					<div class="w-full basis-1/5">{$i18n.t('Code')}</div>
					<div class="w-full basis-1/5 text-center">{$i18n.t('Users')}</div>
					<div class="w-full basis-1/5 text-center">{$i18n.t('Plans')}</div>
				</div>

				<hr class="mt-1.5 border-gray-100 dark:border-gray-850" />

				{#each filteredOrganizations as organization}
					<div class="my-2">
						<OrganizationItem
							{organization}
							showSignupLink={true}
							onEdit={() => {
								selectedOrganization = organization;
								showEditOrganizationModal = true;
							}}
							onDelete={() => deleteOrganizationHandler(organization.id)}
						/>
					</div>
				{/each}
			</div>
		{/if}
	</div>
{/if}
