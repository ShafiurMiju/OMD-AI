<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { getContext, onMount } from 'svelte';
	const i18n = getContext('i18n');

	import Modal from '$lib/components/common/Modal.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';

	export let onSubmit: Function = () => {};

	export let show = false;
	export let edit = false;

	export let plans = [];
	export let organization = null;

	let loading = false;

	export let org_name = '';
	export let org_code = '';
	export let status = 'active';
	export let signup_enabled = true;
	export let selectedPlanIds = [];

	const submitHandler = async () => {
		if (!org_name.trim()) {
			toast.error($i18n.t('Organization name is required'));
			return;
		}

		if (!org_code.trim()) {
			toast.error($i18n.t('Organization code is required'));
			return;
		}

		loading = true;

		const data = {
			org_name: org_name.trim(),
			org_code: org_code.trim(),
			status,
			signup_enabled,
			plans: selectedPlanIds
		};

		await onSubmit(data);

		loading = false;
		show = false;
	};

	const init = () => {
		if (organization) {
			org_name = organization.org_name;
			org_code = organization.org_code;
			status = organization.status || 'active';
			signup_enabled = organization.signup_enabled !== undefined ? organization.signup_enabled : true;
			selectedPlanIds = organization.plans || [];
		} else {
			org_name = '';
			org_code = '';
			status = 'active';
			signup_enabled = true;
			selectedPlanIds = [];
		}
	};

	$: if (show) {
		init();
	}

	onMount(() => {
		init();
	});
</script>

<Modal size="md" bind:show>
	<div>
		<div class=" flex justify-between dark:text-gray-100 px-5 pt-4 mb-1.5">
			<div class=" text-lg font-medium self-center font-primary">
				{#if edit}
					{$i18n.t('Edit Organization')}
				{:else}
					{$i18n.t('Add Organization')}
				{/if}
			</div>
			<button
				class="self-center"
				on:click={() => {
					show = false;
				}}
			>
				<XMark className={'size-5'} />
			</button>
		</div>

		<div class="flex flex-col w-full px-5 pb-4 dark:text-gray-200">
			<form
				class="flex flex-col w-full"
				on:submit={(e) => {
					e.preventDefault();
					submitHandler();
				}}
			>
				<div class="flex flex-col gap-4">
					<!-- Organization Name -->
					<div>
						<label class="block text-sm font-medium mb-2" for="org-name">
							{$i18n.t('Organization Name')} <span class="text-red-500">*</span>
						</label>
						<input
							id="org-name"
							type="text"
							class="w-full rounded-lg px-4 py-2 bg-gray-50 dark:bg-gray-850 dark:text-gray-100 outline-none"
							bind:value={org_name}
							placeholder={$i18n.t('Enter organization name')}
							required
						/>
					</div>

					<!-- Organization Code -->
					<div>
						<label class="block text-sm font-medium mb-2" for="org-code">
							{$i18n.t('Organization Code')} <span class="text-red-500">*</span>
						</label>
						<input
							id="org-code"
							type="text"
							class="w-full rounded-lg px-4 py-2 bg-gray-50 dark:bg-gray-850 dark:text-gray-100 outline-none font-mono"
							bind:value={org_code}
							placeholder={$i18n.t('e.g., ORG001')}
							required
							disabled={edit}
						/>
						{#if edit}
							<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
								{$i18n.t('Organization code cannot be changed')}
							</p>
						{/if}
					</div>

					<!-- Status -->
					<div>
						<label class="block text-sm font-medium mb-2" for="status">
							{$i18n.t('Status')}
						</label>
						<select
							id="status"
							class="w-full rounded-lg px-4 py-2 bg-gray-50 dark:bg-gray-850 dark:text-gray-100 outline-none"
							bind:value={status}
						>
							<option value="active">{$i18n.t('Active')}</option>
							<option value="inactive">{$i18n.t('Inactive')}</option>
							<option value="suspended">{$i18n.t('Suspended')}</option>
						</select>
					</div>

					<!-- Enable Signup -->
					<div>
						<label class="flex items-center gap-2 cursor-pointer">
							<input
								type="checkbox"
								class="rounded"
								bind:checked={signup_enabled}
							/>
							<span class="text-sm font-medium">
								{$i18n.t('Enable organization signup')}
							</span>
						</label>
						<p class="text-xs text-gray-500 dark:text-gray-400 mt-1 ml-6">
							{$i18n.t('Allow users to register using the organization signup link')}
						</p>
					</div>

					<!-- Plans -->
					<div>
						<label class="block text-sm font-medium mb-2">
							{$i18n.t('Subscription Plans')}
						</label>
						<div
							class="w-full rounded-lg px-4 py-2 bg-gray-50 dark:bg-gray-850 max-h-60 overflow-y-auto"
						>
							{#if plans.length === 0}
								<p class="text-sm text-gray-500 dark:text-gray-400">
									{$i18n.t('No plans available')}
								</p>
							{:else}
								{#each plans as plan}
									<label class="flex items-center gap-2 py-1.5 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 rounded px-2">
										<input
											type="checkbox"
											class="rounded"
											value={plan.id}
											checked={selectedPlanIds.includes(plan.id)}
											on:change={(e) => {
												if (e.currentTarget.checked) {
													selectedPlanIds = [...selectedPlanIds, plan.id];
												} else {
													selectedPlanIds = selectedPlanIds.filter((id) => id !== plan.id);
												}
											}}
										/>
										<span class="text-sm">
											{plan.plan_name}
											<span class="text-xs text-gray-500 dark:text-gray-400">
												(${plan.price})
											</span>
										</span>
									</label>
								{/each}
							{/if}
						</div>
					</div>

					<!-- Signup Link Display (when editing and signup is enabled) -->
					{#if edit && signup_enabled}
						<div class="mt-3 p-3 bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800 rounded-lg">
							<div class="text-xs font-medium text-blue-700 dark:text-blue-300 mb-1.5">
								{$i18n.t('Public Signup Link')}:
							</div>
							<div class="flex items-center gap-2">
								<div class="flex-1 min-w-0 text-sm text-blue-600 dark:text-blue-400 font-mono bg-white dark:bg-gray-900 px-2 py-1.5 rounded border border-blue-200 dark:border-blue-800 truncate">
									{`${window.location.origin}/auth?org=${org_code}`}
								</div>
								<button
									type="button"
									class="px-3 py-1.5 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 rounded-md transition-colors whitespace-nowrap"
									on:click={() => {
										navigator.clipboard.writeText(`${window.location.origin}/auth?org=${org_code}`);
										toast.success($i18n.t('Signup link copied to clipboard!'));
									}}
								>
									{$i18n.t('Copy')}
								</button>
							</div>
						</div>
					{/if}

					<!-- Submit Button -->
					<div class="flex justify-end gap-2 pt-2">
						<button
							type="button"
							class="px-4 py-2 rounded-lg text-sm font-medium bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 transition"
							on:click={() => {
								show = false;
							}}
							disabled={loading}
						>
							{$i18n.t('Cancel')}
						</button>
						<button
							type="submit"
							class="px-4 py-2 rounded-lg text-sm font-medium bg-black hover:bg-gray-800 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition"
							disabled={loading}
						>
							{#if loading}
								<div class="flex items-center gap-2">
									<div class="animate-spin rounded-full h-4 w-4 border-2 border-white dark:border-black border-t-transparent" />
									{$i18n.t('Saving...')}
								</div>
							{:else if edit}
								{$i18n.t('Update')}
							{:else}
								{$i18n.t('Create')}
							{/if}
						</button>
					</div>
				</div>
			</form>
		</div>
	</div>
</Modal>
