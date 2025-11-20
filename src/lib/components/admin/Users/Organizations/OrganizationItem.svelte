<script>
	import { toast } from 'svelte-sonner';
	import { getContext } from 'svelte';

	const i18n = getContext('i18n');

	import Pencil from '$lib/components/icons/Pencil.svelte';
	import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
	import User from '$lib/components/icons/User.svelte';
	import CreditCard from '$lib/components/icons/CreditCard.svelte';

	export let organization = {};
	export let onEdit = () => {};
	export let onDelete = () => {};
	export let showSignupLink = false;

	$: signupUrl = `${window.location.origin}/auth?org=${organization.org_code}`;

	const copySignupLink = () => {
		navigator.clipboard.writeText(signupUrl);
		toast.success($i18n.t('Signup link copied to clipboard!'));
	};

	$: userCount = organization.users ? organization.users.length : 0;
	$: planCount = organization.plans ? organization.plans.length : 0;

	const getStatusColor = (status) => {
		switch (status) {
			case 'active':
				return 'text-green-600 dark:text-green-400';
			case 'inactive':
				return 'text-gray-600 dark:text-gray-400';
			case 'suspended':
				return 'text-red-600 dark:text-red-400';
			default:
				return 'text-gray-600 dark:text-gray-400';
		}
	};
</script>

<div class="flex items-center gap-3 justify-between px-1 text-xs w-full transition">
	<div class="flex items-center gap-2 w-full basis-2/5 font-medium">
		<div class="flex flex-col">
			<div class="line-clamp-1 text-sm">{organization.org_name}</div>
			<div class="text-xs {getStatusColor(organization.status)} capitalize">
				{organization.status}
			</div>
		</div>
	</div>

	<div class="w-full basis-1/5 font-mono text-xs text-gray-600 dark:text-gray-400">
		{organization.org_code}
	</div>

	<div class="w-full basis-1/5 text-center flex items-center justify-center gap-1">
		<User className="size-3.5" />
		<span>{userCount}</span>
	</div>

	<div class="w-full basis-1/5 text-center flex items-center justify-center gap-1">
		<CreditCard className="size-3.5" />
		<span>{planCount}</span>
	</div>

	<div class="flex items-center gap-1">
		<button
			class="rounded-lg p-1.5 hover:bg-gray-100 dark:hover:bg-gray-850 transition"
			on:click={onEdit}
			aria-label={$i18n.t('Edit')}
		>
			<Pencil className="size-3.5" />
		</button>

		<button
			class="rounded-lg p-1.5 hover:bg-red-100 dark:hover:bg-red-900/20 text-red-600 transition"
			on:click={() => {
				if (confirm($i18n.t('Are you sure you want to delete this organization?'))) {
					onDelete();
				}
			}}
			aria-label={$i18n.t('Delete')}
		>
			<GarbageBin className="size-3.5" />
		</button>
	</div>

	{#if organization.signup_enabled && showSignupLink}
		<div class="mt-2 px-3 py-2 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
			<div class="flex items-center justify-between gap-2">
				<div class="flex-1 min-w-0">
					<div class="text-xs text-gray-500 dark:text-gray-400 mb-1">
						{$i18n.t('Public Signup Link')}:
					</div>
					<div class="text-sm text-gray-700 dark:text-gray-300 font-mono truncate">
						{signupUrl}
					</div>
				</div>
				<button
					class="px-3 py-1.5 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 rounded-md transition-colors whitespace-nowrap"
					on:click={copySignupLink}
				>
					{$i18n.t('Copy Link')}
				</button>
			</div>
		</div>
	{/if}
</div>
