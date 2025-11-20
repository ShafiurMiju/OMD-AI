<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { getContext, onMount } from 'svelte';
	import type { Writable } from 'svelte/store';
	
	const i18n: Writable<any> = getContext('i18n');

	import Modal from '$lib/components/common/Modal.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	// import { getModels } from '$lib/apis/models';
	import { getModels } from '$lib/apis';

	export let show = false;
	export let edit = false;
	export let plan: any = null;
	export let onSubmit: (data: any) => void = () => {};

	let loading = false;
	let models: any[] = [];
	let selectedModels: string[] = [];

	// Form fields
	let plan_name = '';
	let subtitle = '';
	let plan_type = 'premium';
	let duration_type = 'months';
	let plan_duration = 1;
	let price = 0;
	let benefits = [''];
	let additional_info = '';
	let group = '';
	let is_active = true;

	const loadModels = async () => {
		try {
			const res = await getModels(localStorage.token);
			if (res) {
				models = res.data || res || [];
			}
		} catch (error) {
			console.error('Error loading models:', error);
			toast.error($i18n.t('Failed to load models'));
		}
	};

	const addBenefit = () => {
		benefits = [...benefits, ''];
	};

	const removeBenefit = (index: number) => {
		benefits = benefits.filter((_, i) => i !== index);
	};

	const toggleModel = (modelId: string) => {
		if (selectedModels.includes(modelId)) {
			selectedModels = selectedModels.filter(id => id !== modelId);
		} else {
			selectedModels = [...selectedModels, modelId];
		}
	};

	const selectAllModels = () => {
		if (selectedModels.length === models.length) {
			selectedModels = [];
		} else {
			selectedModels = models.map(m => m.id);
		}
	};

	const submitHandler = async () => {
		// Validate required fields
		if (!plan_name || plan_name.trim() === '') {
			toast.error($i18n.t('Plan name is required'));
			return;
		}

		if (price < 0) {
			toast.error($i18n.t('Price must be 0 or greater'));
			return;
		}

		if (plan_duration < 1) {
			toast.error($i18n.t('Plan duration must be at least 1'));
			return;
		}

		loading = true;

		// Filter out empty benefits
		const filteredBenefits = benefits.filter(b => b && b.trim() !== '');

		const planData = {
			plan_name: plan_name.trim(),
			subtitle: subtitle.trim() || undefined,
			plan_type,
			duration_type,
			plan_duration: parseInt(plan_duration.toString()),
			price: parseFloat(price.toString()),
			benefits: filteredBenefits.length > 0 ? filteredBenefits : undefined,
			additional_info: additional_info.trim() || undefined,
			group: group.trim() || undefined,
			models: selectedModels.length > 0 ? selectedModels : undefined,
			...(edit && { is_active })
		};

		await onSubmit(planData);

		loading = false;
	};

	const init = async () => {
		// Load models
		await loadModels();

		if (edit && plan) {
			plan_name = plan.plan_name || '';
			subtitle = plan.subtitle || '';
			plan_type = plan.plan_type || 'premium';
			duration_type = plan.duration_type || 'months';
			plan_duration = plan.plan_duration || 1;
			price = plan.price || 0;
			additional_info = plan.additional_info || '';
			group = plan.group || '';
			is_active = plan.is_active ?? true;

			// Load selected models
			if (plan.models && Array.isArray(plan.models)) {
				selectedModels = [...plan.models];
			} else {
				selectedModels = [];
			}

			// Convert benefits array to list
			if (plan.benefits && Array.isArray(plan.benefits)) {
				benefits = [...plan.benefits];
			} else {
				benefits = [''];
			}
		} else {
			// Reset for new plan
			plan_name = '';
			subtitle = '';
			plan_type = 'premium';
			duration_type = 'months';
			plan_duration = 1;
			price = 0;
			benefits = [''];
			additional_info = '';
			group = '';
			is_active = true;
			selectedModels = [];
		}
	};

	$: if (show) {
		init();
	}
</script>

<Modal bind:show size="lg">
	<div class="px-6 py-5">
		<div class="flex items-center justify-between mb-1">
			<div class="text-lg font-semibold text-gray-900 dark:text-gray-100">
				{edit ? $i18n.t('Edit Plan') : $i18n.t('Add New Plan')}
			</div>

			<button
				class="self-center p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition"
				on:click={() => {
					show = false;
				}}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
					class="w-5 h-5 text-gray-400"
				>
					<path
						d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
					/>
				</svg>
			</button>
		</div>

		<form
			class="flex flex-col max-h-[70vh] overflow-y-auto space-y-5 scrollbar-hidden mt-5"
			on:submit|preventDefault={submitHandler}
		>
			<!-- Plan Name and Subtitle -->
			<div class="grid grid-cols-2 gap-4">
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" for="plan-name">
						{$i18n.t('Plan Name')}
					</label>
					<input
						id="plan-name"
						type="text"
						class="w-full px-3 py-2.5 text-sm bg-transparent border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 dark:focus:ring-gray-100 focus:border-transparent placeholder-gray-400 dark:placeholder-gray-500"
						placeholder={$i18n.t('e.g., Premium Package')}
						bind:value={plan_name}
						required
					/>
				</div>

				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" for="plan-subtitle">
						{$i18n.t('Subtitle')}
					</label>
					<input
						id="plan-subtitle"
						type="text"
						class="w-full px-3 py-2.5 text-sm bg-transparent border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 dark:focus:ring-gray-100 focus:border-transparent placeholder-gray-400 dark:placeholder-gray-500"
						placeholder={$i18n.t('Short description')}
						bind:value={subtitle}
					/>
				</div>
			</div>

			<!-- Price and Duration -->
			<div class="grid grid-cols-2 gap-4">
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" for="plan-price">
						{$i18n.t('Price ($)')}
					</label>
					<input
						id="plan-price"
						type="number"
						step="0.01"
						min="0"
						class="w-full px-3 py-2.5 text-sm bg-transparent border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 dark:focus:ring-gray-100 focus:border-transparent placeholder-gray-400 dark:placeholder-gray-500"
						bind:value={price}
						required
					/>
				</div>

				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" for="plan-duration">
						{$i18n.t('Duration')}
					</label>
					<input
						id="plan-duration"
						type="number"
						min="1"
						class="w-full px-3 py-2.5 text-sm bg-transparent border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 dark:focus:ring-gray-100 focus:border-transparent placeholder-gray-400 dark:placeholder-gray-500"
						placeholder="1"
						bind:value={plan_duration}
						required
					/>
				</div>
			</div>

			<!-- Duration Type and Select Models -->
			<div class="grid grid-cols-2 gap-4">
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" for="duration-type">
						{$i18n.t('Duration Type')}
					</label>
					<select
						id="duration-type"
						class="w-full px-3 py-2.5 text-sm bg-transparent border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 dark:focus:ring-gray-100 focus:border-transparent appearance-none"
						style="background-image: url('data:image/svg+xml;charset=UTF-8,%3csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 20 20%27 fill=%27gray%27%3e%3cpath fill-rule=%27evenodd%27 d=%27M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z%27 clip-rule=%27evenodd%27/%3e%3c/svg%3e'); background-repeat: no-repeat; background-position: right 0.5rem center; background-size: 1.5em 1.5em; padding-right: 2.5rem;"
						bind:value={duration_type}
					>
						<option value="months">{$i18n.t('months')}</option>
						<option value="days">{$i18n.t('days')}</option>
						<option value="weeks">{$i18n.t('weeks')}</option>
						<option value="years">{$i18n.t('years')}</option>
					</select>
				</div>

				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" for="plan-models">
						{$i18n.t('Select Models')}
					</label>
					<div class="relative">
						<details class="relative">
							<summary class="w-full px-3 py-2.5 text-sm bg-transparent border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 dark:focus:ring-gray-100 focus:border-transparent cursor-pointer list-none flex items-center justify-between">
								<span class={selectedModels.length === 0 ? 'text-gray-400 dark:text-gray-500' : ''}>
									{#if selectedModels.length === 0}
										{$i18n.t('Select models...')}
									{:else if selectedModels.length === models.length}
										{$i18n.t('All Models')} ({models.length})
									{:else}
										{selectedModels.length} {$i18n.t('selected')}
									{/if}
								</span>
								<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-5 h-5 text-gray-400">
									<path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd"/>
								</svg>
							</summary>
							<div class="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg max-h-60 overflow-y-auto" role="listbox" tabindex="-1" on:click|stopPropagation on:keydown|stopPropagation>
								{#if models.length > 0}
									<div class="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-2">
										<button
											type="button"
											class="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded flex items-center gap-2"
											on:click={selectAllModels}
										>
											<input
												type="checkbox"
												checked={selectedModels.length === models.length}
												class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
												on:click|stopPropagation
											/>
											<span class="font-medium">
												{selectedModels.length === models.length ? $i18n.t('Deselect All') : $i18n.t('Select All')}
											</span>
										</button>
									</div>
									{#each models as model}
										<button
											type="button"
											class="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 border-b border-gray-100 dark:border-gray-700 last:border-b-0"
											on:click={() => toggleModel(model.id)}
										>
											<input
												type="checkbox"
												checked={selectedModels.includes(model.id)}
												class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
												on:click|stopPropagation
											/>
											<span class="flex-1 truncate">{model.name || model.id}</span>
										</button>
									{/each}
								{:else}
									<div class="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">
										{$i18n.t('No models available')}
									</div>
								{/if}
							</div>
						</details>
					</div>
				</div>
			</div>

			<!-- Benefits -->
			<div>
				<div class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
					{$i18n.t('Benefits:')}
				</div>
				
				<div class="space-y-2">
					{#each benefits as benefit, index}
						<div class="flex gap-2 items-center">
							<input
								type="text"
								class="flex-1 px-3 py-2.5 text-sm bg-transparent border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 dark:focus:ring-gray-100 focus:border-transparent placeholder-gray-400 dark:placeholder-gray-500"
								placeholder={$i18n.t('Benefit feature')}
								bind:value={benefits[index]}
							/>
							{#if benefits.length > 1}
								<button
									type="button"
									class="p-2 hover:bg-red-50 dark:hover:bg-red-900/20 text-red-500 dark:text-red-400 rounded-lg transition"
									on:click={() => removeBenefit(index)}
								>
									<svg
										xmlns="http://www.w3.org/2000/svg"
										viewBox="0 0 20 20"
										fill="currentColor"
										class="w-5 h-5"
									>
										<path
											fill-rule="evenodd"
											d="M8.75 1A2.75 2.75 0 006 3.75v.443c-.795.077-1.584.176-2.365.298a.75.75 0 10.23 1.482l.149-.022.841 10.518A2.75 2.75 0 007.596 19h4.807a2.75 2.75 0 002.742-2.53l.841-10.52.149.023a.75.75 0 00.23-1.482A41.03 41.03 0 0014 4.193V3.75A2.75 2.75 0 0011.25 1h-2.5zM10 4c.84 0 1.673.025 2.5.075V3.75c0-.69-.56-1.25-1.25-1.25h-2.5c-.69 0-1.25.56-1.25 1.25v.325C8.327 4.025 9.16 4 10 4zM8.58 7.72a.75.75 0 00-1.5.06l.3 7.5a.75.75 0 101.5-.06l-.3-7.5zm4.34.06a.75.75 0 10-1.5-.06l-.3 7.5a.75.75 0 101.5.06l.3-7.5z"
											clip-rule="evenodd"
										/>
									</svg>
								</button>
							{/if}
						</div>
					{/each}
				</div>

				<button
					type="button"
					class="mt-2 text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium transition flex items-center gap-1"
					on:click={addBenefit}
				>
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4">
						<path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
					</svg>
					{$i18n.t('Add Benefit')}
				</button>
			</div>

			<!-- Additional Information -->
			<div>
				<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" for="additional-info">
					{$i18n.t('Additional Information')}
				</label>
				<textarea
					id="additional-info"
					rows="3"
					class="w-full px-3 py-2.5 text-sm bg-transparent border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 dark:focus:ring-gray-100 focus:border-transparent resize-none placeholder-gray-400 dark:placeholder-gray-500"
					placeholder={$i18n.t('Any extra details about the plan')}
					bind:value={additional_info}
				/>
			</div>

			<!-- Active Status (only for edit) -->
			{#if edit}
				<div class="flex items-center space-x-2">
					<input
						id="plan-active"
						type="checkbox"
						class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
						bind:checked={is_active}
					/>
					<label for="plan-active" class="text-sm font-medium text-gray-700 dark:text-gray-300">
						{$i18n.t('Plan is active')}
					</label>
				</div>
			{/if}
		</form>

		<div class="flex justify-end gap-3 pt-5 mt-5 border-t border-gray-200 dark:border-gray-700">
			<button
				type="button"
				class="px-5 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition"
				on:click={() => {
					show = false;
				}}
			>
				{$i18n.t('Cancel')}
			</button>

			<button
				type="button"
				class="px-5 py-2.5 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-lg transition flex items-center gap-2"
				on:click={submitHandler}
				disabled={loading}
			>
				{#if loading}
					<Spinner className="size-4" />
				{/if}
				{edit ? $i18n.t('Update Plan') : $i18n.t('Save Plan')}
			</button>
		</div>
	</div>
</Modal>
