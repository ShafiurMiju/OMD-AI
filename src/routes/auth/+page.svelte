<script lang="ts">
	import DOMPurify from 'dompurify';
	import { marked } from 'marked';

	import { toast } from 'svelte-sonner';

	import { onMount, getContext, tick } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';

	import { getBackendConfig } from '$lib/apis';
	import { ldapUserSignIn, getSessionUser, userSignIn, userSignUp } from '$lib/apis/auths';
	import { getSubscriptionPlans } from '$lib/apis/subscriptions';

	import { WEBUI_API_BASE_URL, WEBUI_BASE_URL } from '$lib/constants';
	import { WEBUI_NAME, config, user, socket } from '$lib/stores';

	import { generateInitialsImage, canvasPixelTest } from '$lib/utils';

	import Spinner from '$lib/components/common/Spinner.svelte';
	import OnBoarding from '$lib/components/OnBoarding.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import SubscriptionPlans from '$lib/components/SubscriptionPlans.svelte';
	import PaymentModal from '$lib/components/PaymentModal.svelte';
	import { redirect } from '@sveltejs/kit';

	const i18n = getContext('i18n');

	let loaded = false;

	let mode = $config?.features.enable_ldap ? 'ldap' : 'signin';

	let form = null;
	let orgCode = null; // Organization code from URL
	let organization = null; // Organization data for signup

	let name = '';
	let email = '';
	let password = '';
	let confirmPassword = '';

	let ldapUsername = '';
	
	// Subscription-related variables
	let subscriptionPlans = [];
	let selectedPlanId = null;
	let showPaymentModal = false;
	let selectedPlan = null;
	let paymentId = null;
	let signupStep = 'credentials'; // 'credentials' | 'plan-selection' | 'payment'

	// Multi-step signup variables
	let currentSignupStep = 1; // 1: Plan Info, 2: Personal Info, 3: Payment
	let selectedPlanType: 'free' | 'paid' = 'free';
	let paymentMethod: 'card' | 'bank' = 'card';
	
	// Personal Information
	let firstName = '';
	let lastName = '';
	let phone = '';
	let dateOfBirth = '';
	
	// Payment Information
	let cardNumber = '';
	let expirationDate = '';
	let cvc = '';
	let bankName = '';
	let accountHolder = '';
	let routingNumber = '';
	let accountNumber = '';
	let agreementChecked = false;

	const setSessionUser = async (sessionUser, redirectPath: string | null = null) => {
		if (sessionUser) {
			console.log(sessionUser);
			toast.success($i18n.t(`You're now logged in.`));
			if (sessionUser.token) {
				localStorage.token = sessionUser.token;
			}
			$socket.emit('user-join', { auth: { token: sessionUser.token } });
			await user.set(sessionUser);
			await config.set(await getBackendConfig());

			if (!redirectPath) {
				redirectPath = $page.url.searchParams.get('redirect') || '/';
			}

			goto(redirectPath);
			localStorage.removeItem('redirectPath');
		}
	};

	const signInHandler = async () => {
		const sessionUser = await userSignIn(email, password).catch((error) => {
			toast.error(`${error}`);
			return null;
		});

		await setSessionUser(sessionUser);
	};

	const loadSubscriptionPlans = async () => {
		try {
			const allPlans = await getSubscriptionPlans();
			
			// If we have an organization, filter plans to only show org plans
			if (organization && organization.plans && organization.plans.length > 0) {
				subscriptionPlans = allPlans.filter((plan) => organization.plans.includes(plan.id));
			} else {
				subscriptionPlans = allPlans;
			}
		} catch (error) {
			console.error('Error loading subscription plans:', error);
			subscriptionPlans = [];
		}
	};

	const loadOrganizationInfo = async (code) => {
		try {
			const res = await fetch(`${WEBUI_API_BASE_URL}/organizations/public/code/${code}`);
			
			if (!res.ok) {
				console.error('Organization not found');
				return;
			}

			organization = await res.json();
		} catch (error) {
			console.error('Error loading organization:', error);
		}
	};
	
	const signUpHandler = async () => {
		if ($config?.features?.enable_signup_password_confirmation) {
			if (password !== confirmPassword) {
				toast.error($i18n.t('Passwords do not match.'));
				return;
			}
		}

		// If subscription plans are available, proceed to plan selection
		if (subscriptionPlans.length > 0 && signupStep === 'credentials') {
			signupStep = 'plan-selection';
			return;
		}

		// Show loading state
		const loadingToast = toast.loading($i18n.t('Creating your account...'));

		try {
			// Complete signup with or without plan
			const result = await userSignUp(
				name, 
				email, 
				password, 
				generateInitialsImage(name),
				selectedPlanId,
				paymentId,
				dateOfBirth,
				phone
			);

			toast.dismiss(loadingToast);

			if (result) {
				// Check if result is a success message (email sent) or session user (auto-login)
				if (result.success && result.message) {
					// Email sent successfully - show message and stay on signup page
					toast.success(result.message);
					
					// Show additional info modal/message
					toast.info($i18n.t('Please check your email inbox (and spam folder) for your temporary password.'), {
						duration: 8000
					});
					
					// Redirect to signin after a delay
					setTimeout(() => {
						mode = 'signin';
						email = result.email || email;
					}, 3000);
				} else {
					// Auto-login for first admin user
					await setSessionUser(result);
				}
			} else {
				toast.error($i18n.t('Account creation failed. Please try again.'));
			}
		} catch (error) {
			toast.dismiss(loadingToast);
			toast.error(`${error}`);
		}
	};

	// Multi-step signup handlers
	const handleSignupContinue = () => {
		if (currentSignupStep === 1) {
			if (!selectedPlanId) {
				toast.error('Please select a subscription plan');
				return;
			}
			currentSignupStep = 2;
		} else if (currentSignupStep === 2) {
			if (!firstName || !lastName || !email || !phone || !dateOfBirth) {
				toast.error('Please fill in all required fields');
				return;
			}
			// Set name from first and last name
			name = `${firstName} ${lastName}`;
			
			// Check if selected plan is free
			const plan = subscriptionPlans.find(p => p.id === selectedPlanId);
			if (plan && (plan.price === 0 || (plan.plan_name || plan.name || '').toLowerCase().includes('free'))) {
				// Skip payment for free plans
				handleCompleteRegistration();
			} else {
				currentSignupStep = 3;
			}
		} else if (currentSignupStep === 3) {
			handleCompleteRegistration();
		}
	};

	const handleSignupBack = () => {
		if (currentSignupStep > 1) {
			currentSignupStep--;
		}
	};

	const handleCompleteRegistration = async () => {
		if (!agreementChecked) {
			toast.error('Please acknowledge the disclaimer');
			return;
		}

		// Generate a temporary password - backend will override this anyway for email signup
		if (!password) {
			password = 'temp_' + Math.random().toString(36).substring(7);
		}

		// Show loading state
		const loadingToast = toast.loading($i18n.t('Creating your account...'));

		try {
			let result;
			
			// Use organization signup endpoint if org code is present
			if (orgCode) {
				const res = await fetch(`${WEBUI_API_BASE_URL}/auths/signup/org/${orgCode}`, {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json'
					},
					body: JSON.stringify({
						name,
						email,
						password,
						plan_id: selectedPlanId || null
					})
				});

				if (!res.ok) {
					const error = await res.json();
					throw new Error(error.detail || 'Signup failed');
				}

				result = await res.json();
			} else {
				// Regular signup
				result = await userSignUp(
					name, 
					email, 
					password, 
					generateInitialsImage(name),
					selectedPlanId,
					paymentId,
					dateOfBirth,
					phone
				);
			}

			toast.dismiss(loadingToast);

			if (result) {
				// Check if result is a success message (email sent) or session user (auto-login)
				if (result.success && result.message) {
					// Email sent successfully - show message
					toast.success(result.message);
					
					// Show additional info
					toast.info($i18n.t('Please check your email inbox (and spam folder) for your temporary password.'), {
						duration: 8000
					});
					
					// Redirect to signin after a delay
					setTimeout(() => {
						mode = 'signin';
						email = result.email || email;
						currentSignupStep = 1; // Reset signup flow
						orgCode = null; // Clear org code
					}, 3000);
				} else {
					// Auto-login for first admin user only
					await setSessionUser(result);
				}
			} else {
				toast.error($i18n.t('Account creation failed. Please try again.'));
			}
		} catch (error) {
			toast.dismiss(loadingToast);
			toast.error(`${error}`);
		}
	};

	const formatPhoneNumber = (value: string) => {
		const cleaned = value.replace(/\D/g, '');
		const match = cleaned.match(/^(\d{0,3})(\d{0,3})(\d{0,4})$/);
		if (match) {
			const formatted = !match[2] ? match[1] : `(${match[1]}) ${match[2]}${match[3] ? '-' + match[3] : ''}`;
			return formatted;
		}
		return value;
	};

	const handlePhoneInput = (e: Event) => {
		const target = e.target as HTMLInputElement;
		phone = formatPhoneNumber(target.value);
	};

	const formatCardNumber = (value: string) => {
		const cleaned = value.replace(/\s/g, '');
		const match = cleaned.match(/.{1,4}/g);
		return match ? match.join(' ') : cleaned;
	};

	const handleCardInput = (e: Event) => {
		const target = e.target as HTMLInputElement;
		cardNumber = formatCardNumber(target.value.replace(/\D/g, ''));
	};

	const formatExpiration = (value: string) => {
		const cleaned = value.replace(/\D/g, '');
		if (cleaned.length >= 2) {
			return cleaned.substring(0, 2) + '/' + cleaned.substring(2, 4);
		}
		return cleaned;
	};

	const handleExpirationInput = (e: Event) => {
		const target = e.target as HTMLInputElement;
		expirationDate = formatExpiration(target.value);
	};
	
	const handlePlanSelect = (planId: string) => {
		selectedPlanId = planId;
		selectedPlan = subscriptionPlans.find(p => p.id === planId);
	};
	
	const proceedWithSelectedPlan = () => {
		if (!selectedPlanId) {
			toast.error('Please select a subscription plan');
			return;
		}
		
		// Show payment modal
		signupStep = 'payment';
		showPaymentModal = true;
	};
	
	const handlePaymentSuccess = async (pId: string) => {
		paymentId = pId;
		showPaymentModal = false;
		
		// Complete signup with payment
		await signUpHandler();
	};
	
	const handlePaymentCancel = () => {
		showPaymentModal = false;
		signupStep = 'plan-selection';
	};
	
	const skipPlanSelection = async () => {
		// Allow signup without subscription (free tier)
		selectedPlanId = null;
		await signUpHandler();
	};

	const ldapSignInHandler = async () => {
		const sessionUser = await ldapUserSignIn(ldapUsername, password).catch((error) => {
			toast.error(`${error}`);
			return null;
		});
		await setSessionUser(sessionUser);
	};

	const submitHandler = async () => {
		if (mode === 'ldap') {
			await ldapSignInHandler();
		} else if (mode === 'signin') {
			await signInHandler();
		} else {
			await signUpHandler();
		}
	};

	const oauthCallbackHandler = async () => {
		// Get the value of the 'token' cookie
		function getCookie(name) {
			const match = document.cookie.match(
				new RegExp('(?:^|; )' + name.replace(/([.$?*|{}()[\]\\/+^])/g, '\\$1') + '=([^;]*)')
			);
			return match ? decodeURIComponent(match[1]) : null;
		}

		const token = getCookie('token');
		if (!token) {
			return;
		}

		const sessionUser = await getSessionUser(token).catch((error) => {
			toast.error(`${error}`);
			return null;
		});

		if (!sessionUser) {
			return;
		}

		localStorage.token = token;
		await setSessionUser(sessionUser, localStorage.getItem('redirectPath') || null);
	};

	let onboarding = false;

	async function setLogoImage() {
		await tick();
		const logoLeft = document.getElementById('logo-left');
		const logoMobile = document.getElementById('logo-mobile');

		const updateLogo = (logo) => {
			if (!logo) return;
			
			const isDarkMode = document.documentElement.classList.contains('dark');

			if (isDarkMode) {
				const darkImage = new Image();
				darkImage.src = `${WEBUI_BASE_URL}/static/favicon-dark.png`;

				darkImage.onload = () => {
					logo.src = `${WEBUI_BASE_URL}/static/favicon-dark.png`;
					logo.style.filter = ''; // Ensure no inversion is applied if favicon-dark.png exists
				};

				darkImage.onerror = () => {
					logo.style.filter = 'invert(1)'; // Invert image if favicon-dark.png is missing
				};
			} else {
				logo.src = `${WEBUI_BASE_URL}/static/favicon.png`;
				logo.style.filter = '';
			}
		};

		updateLogo(logoLeft);
		updateLogo(logoMobile);
	}

	onMount(async () => {
		const redirectPath = $page.url.searchParams.get('redirect');
		if ($user !== undefined) {
			goto(redirectPath || '/');
		} else {
			if (redirectPath) {
				localStorage.setItem('redirectPath', redirectPath);
			}
		}

		const error = $page.url.searchParams.get('error');
		if (error) {
			toast.error(error);
		}

		await oauthCallbackHandler();
		form = $page.url.searchParams.get('form');
		
		// Check for organization code
		orgCode = $page.url.searchParams.get('org');
		if (orgCode) {
			await loadOrganizationInfo(orgCode);
			mode = 'signup'; // Force signup mode for organization
		}
		
		// Load subscription plans (will be filtered by org if applicable)
		await loadSubscriptionPlans();

		loaded = true;
		setLogoImage();

		if (($config?.features.auth_trusted_header ?? false) || $config?.features.auth === false) {
			await signInHandler();
		} else {
			onboarding = $config?.onboarding ?? false;
		}
	});
</script>

<svelte:head>
	<title>
		{`${$WEBUI_NAME}`}
	</title>
</svelte:head>

<OnBoarding
	bind:show={onboarding}
	getStartedHandler={() => {
		onboarding = false;
		mode = $config?.features.enable_ldap ? 'ldap' : 'signup';
	}}
/>

<div class="w-full h-screen max-h-[100dvh] text-white relative" id="auth-page">
	<div class="w-full h-full absolute top-0 left-0 bg-white dark:bg-gray-950"></div>

	<div class="w-full absolute top-0 left-0 right-0 h-8 drag-region" />

	{#if loaded}
		<div
			class="fixed inset-0 bg-transparent w-full h-full flex font-primary z-50 text-black dark:text-white overflow-y-auto"
			id="auth-container"
		>
			<div class="w-full min-h-full flex flex-col lg:flex-row"
			>
				{#if ($config?.features.auth_trusted_header ?? false) || $config?.features.auth === false}
					<div class="w-full flex items-center justify-center px-6 py-10">
						<div class="w-full max-w-md">
							<div
								class="flex items-center justify-center gap-3 text-xl sm:text-2xl text-center font-semibold dark:text-gray-200"
							>
								<div>
									{$i18n.t('Signing in to {{WEBUI_NAME}}', { WEBUI_NAME: $WEBUI_NAME })}
								</div>

								<div>
									<Spinner className="size-5" />
								</div>
							</div>
						</div>
					</div>
				{:else}
					<!-- Left Side - Branding (Only for Sign In, hidden for Signup) -->
					{#if mode !== 'signup'}
						<div class="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-12 flex-col justify-center items-center">
							<div class="max-w-xl text-center">
								<!-- Logo -->
								<div class="mb-8 flex justify-center">
									<img
										id="logo-left"
										crossorigin="anonymous"
										src="{WEBUI_BASE_URL}/static/favicon.png"
										class="h-16 w-16 rounded-full"
										alt="OptimalMD Logo"
									/>
								</div>
								
								<!-- Main Heading -->
								<h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-4">
									My AI Doctor™ - Your Diagnostic Companion
								</h1>
								
								<!-- Subheading -->
								<p class="text-xl text-gray-600 dark:text-gray-300">
									Get Insights into Your Health Journey
								</p>
							</div>
						</div>
					{/if}

					<!-- Right Side - Form (Full width for signup, half width for signin) -->
					<div class="w-full {mode === 'signup' ? '' : 'lg:w-1/2'} flex {mode === 'signup' ? 'items-start' : 'items-center'} justify-center px-6 {mode === 'signup' ? 'py-6 pb-20' : 'py-10'} lg:px-12">
						<div class="w-full {mode === 'signup' ? 'max-w-5xl' : 'max-w-md'} dark:text-gray-100">
							<!-- Mobile Logo - Only visible on mobile -->
							<div class="lg:hidden flex justify-center mb-8">
								<img
									id="logo-mobile"
									crossorigin="anonymous"
									src="{WEBUI_BASE_URL}/static/favicon.png"
									class="h-16 w-16 rounded-full"
									alt="OptimalMD Logo"
								/>
							</div>

							<!-- Mobile Title - Only visible on mobile -->
							<div class="lg:hidden mb-8 text-center">
								<h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
									My AI Doctor™
								</h1>
								<p class="text-sm text-gray-600 dark:text-gray-400">
									Your Diagnostic Companion
								</p>
							</div>

							{#if mode === 'signup'}
								<!-- Multi-step Signup Process -->
								<div class="mb-8 w-full">
									<!-- Logo for Signup -->
									<div class="flex justify-center mb-6">
										<img
											crossorigin="anonymous"
											src="{WEBUI_BASE_URL}/static/favicon.png"
											class="h-12 w-12 sm:h-16 sm:w-16 rounded-full"
											alt="OptimalMD Logo"
										/>
									</div>

									<!-- Title -->
									<div class="text-center mb-6">
										<h1 class="text-xl sm:text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white mb-2">
											{#if organization}
												Join {organization.org_name}
											{:else}
												Create Your Account
											{/if}
										</h1>
										<p class="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
											{#if organization}
												Create your account to access {organization.org_name}
											{:else}
												Join OptimalMD - Your AI-Powered Health Companion
											{/if}
										</p>
									</div>

									<!-- Progress Steps -->
									<div class="w-full mb-8 px-4">
										<div class="relative">
											<!-- Progress Bar Background -->
											<div class="absolute top-6 left-0 right-0 h-1 bg-gray-300 dark:bg-gray-600 rounded-full"></div>
											
											<!-- Progress Bar Fill -->
											<div 
												class="absolute top-6 left-0 h-1 bg-green-600 rounded-full transition-all duration-500 ease-in-out"
												style="width: {currentSignupStep === 1 ? '0%' : currentSignupStep === 2 ? '50%' : '100%'}"
											></div>

											<!-- Steps Container -->
											<div class="relative flex items-center justify-between">
												<!-- Step 1 -->
												<div class="flex flex-col items-start flex-1">
													<div
														class="w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 shadow-lg border-4 border-white dark:border-gray-900 {currentSignupStep >= 1
															? 'bg-green-600 text-white'
															: 'bg-gray-300 dark:bg-gray-600 text-gray-600 dark:text-gray-400'}"
													>
														{#if currentSignupStep > 1}
															<svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
																<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
															</svg>
														{:else}
															<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
																<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
															</svg>
														{/if}
													</div>
													<span class="text-xs sm:text-sm mt-3 font-semibold {currentSignupStep >= 1 ? 'text-green-600' : 'text-gray-500 dark:text-gray-400'}">Plan Info</span>
												</div>

												<!-- Step 2 -->
												<div class="flex flex-col items-center flex-1">
													<div
														class="w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 shadow-lg border-4 border-white dark:border-gray-900 {currentSignupStep >= 2
															? 'bg-green-600 text-white'
															: 'bg-gray-300 dark:bg-gray-600 text-gray-600 dark:text-gray-400'}"
													>
														{#if currentSignupStep > 2}
															<svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
																<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
															</svg>
														{:else}
															<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
																<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
															</svg>
														{/if}
													</div>
													<span class="text-xs sm:text-sm mt-3 font-semibold {currentSignupStep >= 2 ? 'text-green-600' : 'text-gray-500 dark:text-gray-400'}">Personal Information</span>
												</div>

												<!-- Step 3 -->
												<div class="flex flex-col items-end flex-1">
													<div
														class="w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 shadow-lg border-4 border-white dark:border-gray-900 {currentSignupStep >= 3
															? 'bg-green-600 text-white'
															: 'bg-gray-300 dark:bg-gray-600 text-gray-600 dark:text-gray-400'}"
													>
														{#if currentSignupStep > 3}
															<svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
																<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
															</svg>
														{:else}
															<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
																<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
													</svg>
														{/if}
													</div>
													<span class="text-xs sm:text-sm mt-3 font-semibold {currentSignupStep >= 3 ? 'text-green-600' : 'text-gray-500 dark:text-gray-400'}">Payment</span>
												</div>
											</div>
										</div>
									</div>

									{#if currentSignupStep === 1}
										<!-- Step 1: Plan Selection from Database -->
										<div class="space-y-4">
											{#if subscriptionPlans.length === 0}
												<div class="text-center py-8">
													<p class="text-gray-600 dark:text-gray-300">Loading subscription plans...</p>
												</div>
											{:else}
												<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
													{#each subscriptionPlans as plan}
														<button
															type="button"
															on:click={() => {
																selectedPlanId = plan.id;
																selectedPlan = plan;
															}}
															class="relative p-4 sm:p-6 border-2 rounded-xl text-left transition-all hover:shadow-lg {selectedPlanId === plan.id
																? 'border-green-600 bg-green-50 dark:bg-green-900/20'
																: 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700'}"
														>
															<div class="absolute top-4 right-4">
																<span class="inline-block px-3 py-1 bg-green-600 text-white text-xs font-semibold rounded-full">
																	{#if plan.price === 0 || (plan.plan_name || plan.name || '').toLowerCase().includes('free')}
																		Free
																	{:else}
																		${plan.price} / {plan.duration_type || plan.interval || 'month'}
																	{/if}
																</span>
															</div>

															<h3 class="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white mb-2">{plan.plan_name || plan.name}</h3>
															{#if plan.subtitle || plan.description}
																<p class="text-gray-600 dark:text-gray-300 text-sm mb-4">
																	{plan.subtitle || plan.description}
																</p>
															{/if}

															{#if plan.benefits || plan.features}
																<div class="space-y-2">
																	<h4 class="font-semibold text-gray-900 dark:text-white text-sm">Features</h4>
																	<ul class="space-y-1 text-sm text-gray-600 dark:text-gray-300">
																		{#if plan.benefits && Array.isArray(plan.benefits)}
																			{#each plan.benefits as benefit}
																				<li class="flex items-start">
																					<svg class="w-4 h-4 mr-2 mt-0.5 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
																						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
																					</svg>
																					<span>{benefit}</span>
																				</li>
																			{/each}
																		{:else if plan.features}
																			{#if plan.features.maxChats}
																				<li class="flex items-start">
																					<svg class="w-4 h-4 mr-2 mt-0.5 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
																						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
																					</svg>
																					<span>{plan.features.maxChats === -1 ? 'Unlimited chats' : `${plan.features.maxChats} chats`}</span>
																				</li>
																			{/if}
																			{#if plan.features.maxModels}
																				<li class="flex items-start">
																					<svg class="w-4 h-4 mr-2 mt-0.5 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
																						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
																					</svg>
																					<span>{plan.features.maxModels === -1 ? 'All AI models' : `${plan.features.maxModels} AI models`}</span>
																				</li>
																			{/if}
																			{#if plan.features.prioritySupport}
																				<li class="flex items-start">
																					<svg class="w-4 h-4 mr-2 mt-0.5 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
																						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
																					</svg>
																					<span>Priority support</span>
																				</li>
																			{/if}
																			{#if plan.features.customFeatures && Array.isArray(plan.features.customFeatures)}
																				{#each plan.features.customFeatures as feature}
																					<li class="flex items-start">
																						<svg class="w-4 h-4 mr-2 mt-0.5 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
																							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
																						</svg>
																						<span>{feature}</span>
																					</li>
																				{/each}
																			{/if}
																		{/if}
																	</ul>
																</div>
															{/if}

															{#if selectedPlanId === plan.id}
																<div class="mt-4 flex items-center justify-center">
																	<svg class="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
																		<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
																	</svg>
																	<span class="ml-2 font-semibold text-green-600">Selected</span>
																</div>
															{/if}
														</button>
													{/each}
												</div>
											{/if}
										</div>
									{:else if currentSignupStep === 2}
										<!-- Step 2: Personal Information -->
										<div class="space-y-4">
											<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
												<div>
													<label for="firstName" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
														First name<span class="text-red-500">*</span>
													</label>
													<input
														type="text"
														id="firstName"
														bind:value={firstName}
														placeholder="Enter your first name"
														class="w-full px-4 py-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
														required
													/>
												</div>

												<div>
													<label for="lastName" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
														Last name<span class="text-red-500">*</span>
													</label>
													<input
														type="text"
														id="lastName"
														bind:value={lastName}
														placeholder="Enter your last name"
														class="w-full px-4 py-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
														required
													/>
												</div>
											</div>

											<div>
												<label for="email" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
													Email address<span class="text-red-500">*</span>
												</label>
												<input
													type="email"
													id="email"
													bind:value={email}
													placeholder="Enter your email address"
													class="w-full px-4 py-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
													required
												/>
											</div>

											<div>
												<label for="phone" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
													Phone number<span class="text-red-500">*</span>
												</label>
												<input
													type="tel"
													id="phone"
													bind:value={phone}
													on:input={handlePhoneInput}
													placeholder="(xxx) xxx-xxxx"
													maxlength="14"
													class="w-full px-4 py-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
													required
												/>
											</div>

											<div>
												<label for="dob" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
													Date of birth<span class="text-red-500">*</span>
												</label>
												<input
													type="date"
													id="dob"
													bind:value={dateOfBirth}
													class="w-full px-4 py-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
													required
												/>
											</div>
										</div>
									{:else if currentSignupStep === 3}
										<!-- Step 3: Payment -->
										<div class="space-y-4">
											{#if selectedPlan && selectedPlan.price > 0}
												<!-- Show plan summary -->
												<div class="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg mb-4">
													<h4 class="font-semibold text-gray-900 dark:text-white mb-2">Selected Plan</h4>
													<p class="text-lg font-bold text-gray-900 dark:text-white">{selectedPlan.plan_name || selectedPlan.name}</p>
													<p class="text-2xl font-bold text-green-600 dark:text-green-400">
														${selectedPlan.price.toFixed(2)} 
														<span class="text-sm font-normal text-gray-600 dark:text-gray-400">
															/ {selectedPlan.duration_type || selectedPlan.interval || 'month'}
														</span>
													</p>
												</div>

												<!-- Payment Method Toggle -->
												<div class="flex justify-center space-x-4 mb-4">
													<button
														type="button"
														on:click={() => (paymentMethod = 'card')}
														class="flex items-center px-4 py-2 rounded-lg border-2 transition-all text-sm {paymentMethod === 'card'
															? 'border-green-600 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300'
															: 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300'}"
													>
														<svg class="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
															<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
														</svg>
														Card
													</button>

													<button
														type="button"
														on:click={() => (paymentMethod = 'bank')}
														class="flex items-center px-4 py-2 rounded-lg border-2 transition-all text-sm {paymentMethod === 'bank'
															? 'border-green-600 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300'
															: 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300'}"
													>
														<svg class="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
															<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" />
														</svg>
														Bank
													</button>
												</div>

												{#if paymentMethod === 'card'}
													<!-- Card Payment Form -->
													<div class="space-y-4">
														<div>
															<label for="cardNumber" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
																Card number<span class="text-red-500">*</span>
															</label>
															<input
																type="text"
																id="cardNumber"
																bind:value={cardNumber}
																on:input={handleCardInput}
																placeholder="xxxx xxxx xxxx xxxx"
																maxlength="19"
																class="w-full px-4 py-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
															/>
														</div>

														<div class="grid grid-cols-2 gap-4">
															<div>
																<label for="expiration" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
																	Expiration (MM/YY)<span class="text-red-500">*</span>
																</label>
																<input
																	type="text"
																	id="expiration"
																	bind:value={expirationDate}
																	on:input={handleExpirationInput}
																	placeholder="MM/YY"
																	maxlength="5"
																	class="w-full px-4 py-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
																/>
															</div>

															<div>
																<label for="cvc" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
																	CVC<span class="text-red-500">*</span>
																</label>
																<input
																	type="text"
																	id="cvc"
																	bind:value={cvc}
																	placeholder="123"
																	maxlength="4"
																	class="w-full px-4 py-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
																/>
															</div>
														</div>
													</div>
												{:else}
													<!-- Bank Payment Form -->
													<div class="space-y-4">
														<div>
															<label for="bankName" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
																Bank name<span class="text-red-500">*</span>
															</label>
															<input
																type="text"
																id="bankName"
																bind:value={bankName}
																placeholder="Bank"
																class="w-full px-4 py-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
															/>
														</div>

														<div>
															<label for="accountHolder" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
																Account holder<span class="text-red-500">*</span>
															</label>
															<input
																type="text"
																id="accountHolder"
																bind:value={accountHolder}
																placeholder="Account name"
																class="w-full px-4 py-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
															/>
														</div>

														<div>
															<label for="routingNumber" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
																Routing number<span class="text-red-500">*</span>
															</label>
															<input
																type="text"
																id="routingNumber"
																bind:value={routingNumber}
																placeholder="Routing number"
																maxlength="9"
																class="w-full px-4 py-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
															/>
														</div>

														<div>
															<label for="accountNumber" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
																Account number<span class="text-red-500">*</span>
															</label>
															<input
																type="text"
																id="accountNumber"
																bind:value={accountNumber}
																placeholder="Account number"
																class="w-full px-4 py-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
															/>
														</div>
													</div>
												{/if}
											{:else}
												<!-- Free Plan - No payment needed -->
												<div class="text-center py-6">
													<div class="inline-flex items-center justify-center w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full mb-4">
														<svg class="w-8 h-8 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
															<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
														</svg>
													</div>
													<h3 class="text-xl font-bold text-gray-900 dark:text-white mb-2">
														{selectedPlan ? (selectedPlan.plan_name || selectedPlan.name) : 'Free Plan Selected'}
													</h3>
													<p class="text-gray-600 dark:text-gray-300 text-sm">
														No payment required. Your account will be created with the free plan.
													</p>
												</div>
											{/if}

											<!-- Disclaimer -->
											<div class="flex items-start space-x-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
												<input
													type="checkbox"
													id="agreement"
													bind:checked={agreementChecked}
													class="mt-1 h-4 w-4 text-green-600 border-gray-300 dark:border-gray-600 rounded focus:ring-green-500"
												/>
												<label for="agreement" class="text-xs text-gray-600 dark:text-gray-300">
													By entering this site, you fully acknowledge this is not medical advice and not intended to replace
													the relationship with your physician. OptimalMD accepts no responsibility for actions taken based on
													the information gained from this AI diagnostic tool. It is for educational and research use only.
													<button type="button" class="text-blue-600 dark:text-blue-400 hover:underline ml-1">Show less</button>
												</label>
											</div>
										</div>
									{/if}

									<!-- Navigation Buttons -->
									<div class="flex gap-3 mt-6">
										{#if currentSignupStep > 1}
											<button
												type="button"
												on:click={handleSignupBack}
												class="flex-1 px-4 py-3 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 font-semibold rounded-lg transition-all text-sm"
											>
												Back
											</button>
										{/if}

										<button
											type="button"
											on:click={handleSignupContinue}
											class="flex-1 px-4 py-3 bg-gray-900 dark:bg-gray-700 hover:bg-gray-800 dark:hover:bg-gray-600 text-white font-semibold rounded-lg transition-all text-sm"
										>
											{currentSignupStep < 3 ? 'Continue' : 'Complete registration'}
										</button>
									</div>

									<!-- Sign In Link -->
									{#if currentSignupStep === 1}
										<div class="text-center mt-4">
											<span class="text-sm text-gray-600 dark:text-gray-400">Already have an account?</span>
											<button
												type="button"
												class="text-sm text-green-600 dark:text-green-400 hover:underline ml-1 font-semibold"
												on:click={() => {
													mode = 'signin';
													currentSignupStep = 1;
												}}
											>
												Sign in
											</button>
										</div>
									{/if}
								</div>
							{:else}
								<!-- Regular Sign In / LDAP Form -->
								<form
									class="flex flex-col"
									on:submit={(e) => {
										e.preventDefault();
										submitHandler();
									}}
								>
									<!-- Form Title -->
									<div class="mb-6">
										<h2 class="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">
											{#if $config?.onboarding ?? false}
												OptimalMD Member Registration
											{:else if mode === 'ldap'}
												OptimalMD Member Login
											{:else if mode === 'signin'}
												OptimalMD Member Login
											{:else}
												OptimalMD Member Registration
											{/if}
										</h2>

										{#if $config?.onboarding ?? false}
											<div class="mt-2 text-xs font-medium text-gray-600 dark:text-gray-400">
												ⓘ {$WEBUI_NAME}
												{$i18n.t(
													'does not make any external connections, and your data stays securely on your locally hosted server.'
												)}
											</div>
										{/if}
									</div>

								{#if $config?.features.enable_login_form || $config?.features.enable_ldap || form}
									<div class="flex flex-col space-y-4">
										{#if mode === 'signup'}
											<div>
												<label for="name" class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
													>{$i18n.t('Name')}</label
												>
												<input
													bind:value={name}
													type="text"
													id="name"
													class="w-full px-4 py-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
													autocomplete="name"
													placeholder={$i18n.t('Enter Your Full Name')}
													required
												/>
											</div>
										{/if}

										{#if mode === 'ldap'}
											<div>
												<label for="username" class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
													>{$i18n.t('Username')}</label
												>
												<input
													bind:value={ldapUsername}
													type="text"
													class="w-full px-4 py-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
													autocomplete="username"
													name="username"
													id="username"
													placeholder={$i18n.t('Enter Your Username')}
													required
												/>
											</div>
										{:else}
											<div>
												<label for="email" class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
													>{$i18n.t('Email Address')} <span class="text-red-500">*</span></label
												>
												<input
													bind:value={email}
													type="email"
													id="email"
													class="w-full px-4 py-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
													autocomplete="email"
													name="email"
													placeholder="Use your OptimalMD email address."
													required
												/>
											</div>
										{/if}

										<div>
											<label for="password" class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
												>{$i18n.t('Password')}</label
											>
											<SensitiveInput
												bind:value={password}
												type="password"
												id="password"
												inputClassName="w-full px-4 py-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
												placeholder={$i18n.t('Enter Your Password')}
												required
											/>
											{#if mode === 'signin'}
												<div class="mt-2 text-right">
													<button type="button" class="text-sm text-gray-600 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-400 transition">
														Forgot password?
													</button>
												</div>
											{/if}
										</div>

										{#if mode === 'signup' && $config?.features?.enable_signup_password_confirmation}
											<div>
												<label
													for="confirm-password"
													class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block"
													>{$i18n.t('Confirm Password')}</label
												>
												<SensitiveInput
													bind:value={confirmPassword}
													type="password"
													id="confirm-password"
													inputClassName="w-full px-4 py-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
													placeholder={$i18n.t('Confirm Your Password')}
													required
												/>
											</div>
										{/if}

										{#if mode === 'signin'}
											<!-- Disclaimer Checkbox -->
											<div class="flex items-start">
												<input
													type="checkbox"
													id="disclaimer"
													class="mt-1 h-4 w-4 text-green-600 border-gray-300 dark:border-gray-600 rounded focus:ring-green-500"
													required
												/>
												<label for="disclaimer" class="ml-2 text-xs text-gray-600 dark:text-gray-400">
													By entering this site, you fully acknowledge this is not medical advice and not intended to replace the relationship with your physician. OptimalMD accepts no responsibility for actions taken based on the information gained from this AI diagnostic tool. It is for educational and research use only. 
													<button type="button" class="text-blue-600 dark:text-blue-400 hover:underline">Show less</button>
												</label>
											</div>
										{/if}
									</div>
								{/if}
								<div class="mt-6">
									{#if $config?.features.enable_login_form || $config?.features.enable_ldap || form}
										{#if mode === 'ldap'}
											<button
												class="w-full bg-green-700 hover:bg-green-800 dark:bg-green-600 dark:hover:bg-green-700 text-white font-semibold py-3 px-4 rounded-lg transition duration-200 ease-in-out transform hover:scale-[1.02] focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
												type="submit"
											>
												{$i18n.t('Authenticate')}
											</button>
										{:else}
											<button
												class="w-full bg-green-700 hover:bg-green-800 dark:bg-green-600 dark:hover:bg-green-700 text-white font-semibold py-3 px-4 rounded-lg transition duration-200 ease-in-out transform hover:scale-[1.02] focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
												type="submit"
											>
												{mode === 'signin'
													? $i18n.t('Login')
													: ($config?.onboarding ?? false)
														? $i18n.t('Create Admin Account')
														: $i18n.t('Create Account')}
											</button>

											{#if $config?.features.enable_signup && !($config?.onboarding ?? false)}
												<div class="mt-6 text-sm text-center text-gray-600 dark:text-gray-400">
													{mode === 'signin'
														? $i18n.t("Don't have an account?")
														: $i18n.t('Already have an account?')}

													<button
														class="font-semibold text-green-700 dark:text-green-500 hover:text-green-800 dark:hover:text-green-400 ml-1 transition"
														type="button"
														on:click={() => {
															if (mode === 'signin') {
																mode = 'signup';
															} else {
																mode = 'signin';
															}
														}}
													>
														{mode === 'signin' ? $i18n.t('Sign up') : $i18n.t('Sign in')}
													</button>
												</div>
											{/if}
										{/if}
									{/if}
								</div>
							</form>
							{/if}

							{#if Object.keys($config?.oauth?.providers ?? {}).length > 0}
								<div class="inline-flex items-center justify-center w-full my-6">
									<hr class="flex-1 h-px border-0 bg-gray-300 dark:bg-gray-600" />
									{#if $config?.features.enable_login_form || $config?.features.enable_ldap || form}
										<span
											class="px-4 text-sm font-medium text-gray-500 dark:text-gray-400 bg-transparent"
											>{$i18n.t('or')}</span
										>
									{/if}

									<hr class="flex-1 h-px border-0 bg-gray-300 dark:bg-gray-600" />
								</div>
								<div class="flex flex-col space-y-3">
									{#if $config?.oauth?.providers?.google}
										<button
											class="flex justify-center items-center border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 transition w-full rounded-lg font-medium text-sm py-3 px-4"
											on:click={() => {
												window.location.href = `${WEBUI_BASE_URL}/oauth/google/login`;
											}}
										>
											<svg
												xmlns="http://www.w3.org/2000/svg"
												viewBox="0 0 48 48"
												class="size-5 mr-3"
											>
												<path
													fill="#EA4335"
													d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"
												/><path
													fill="#4285F4"
													d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"
												/><path
													fill="#FBBC05"
													d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"
												/><path
													fill="#34A853"
													d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"
												/><path fill="none" d="M0 0h48v48H0z" />
											</svg>
											<span>{$i18n.t('Continue with {{provider}}', { provider: 'Google' })}</span>
										</button>
									{/if}
									{#if $config?.oauth?.providers?.microsoft}
										<button
											class="flex justify-center items-center border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 transition w-full rounded-lg font-medium text-sm py-3 px-4"
											on:click={() => {
												window.location.href = `${WEBUI_BASE_URL}/oauth/microsoft/login`;
											}}
										>
											<svg
												xmlns="http://www.w3.org/2000/svg"
												viewBox="0 0 21 21"
												class="size-5 mr-3"
											>
												<rect x="1" y="1" width="9" height="9" fill="#f25022" /><rect
													x="1"
													y="11"
													width="9"
													height="9"
													fill="#00a4ef"
												/><rect x="11" y="1" width="9" height="9" fill="#7fba00" /><rect
													x="11"
													y="11"
													width="9"
													height="9"
													fill="#ffb900"
												/>
											</svg>
											<span>{$i18n.t('Continue with {{provider}}', { provider: 'Microsoft' })}</span
											>
										</button>
									{/if}
									{#if $config?.oauth?.providers?.github}
										<button
											class="flex justify-center items-center border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 transition w-full rounded-lg font-medium text-sm py-3 px-4"
											on:click={() => {
												window.location.href = `${WEBUI_BASE_URL}/oauth/github/login`;
											}}
										>
											<svg
												xmlns="http://www.w3.org/2000/svg"
												viewBox="0 0 24 24"
												class="size-5 mr-3"
											>
												<path
													fill="currentColor"
													d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.92 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57C20.565 21.795 24 17.31 24 12c0-6.63-5.37-12-12-12z"
												/>
											</svg>
											<span>{$i18n.t('Continue with {{provider}}', { provider: 'GitHub' })}</span>
										</button>
									{/if}
									{#if $config?.oauth?.providers?.oidc}
										<button
											class="flex justify-center items-center border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 transition w-full rounded-lg font-medium text-sm py-3 px-4"
											on:click={() => {
												window.location.href = `${WEBUI_BASE_URL}/oauth/oidc/login`;
											}}
										>
											<svg
												xmlns="http://www.w3.org/2000/svg"
												fill="none"
												viewBox="0 0 24 24"
												stroke-width="1.5"
												stroke="currentColor"
												class="size-5 mr-3"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													d="M15.75 5.25a3 3 0 0 1 3 3m3 0a6 6 0 0 1-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1 1 21.75 8.25Z"
												/>
											</svg>

											<span
												>{$i18n.t('Continue with {{provider}}', {
													provider: $config?.oauth?.providers?.oidc ?? 'SSO'
												})}</span
											>
										</button>
									{/if}
									{#if $config?.oauth?.providers?.feishu}
										<button
											class="flex justify-center items-center border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 transition w-full rounded-lg font-medium text-sm py-3 px-4"
											on:click={() => {
												window.location.href = `${WEBUI_BASE_URL}/oauth/feishu/login`;
											}}
										>
											<span>{$i18n.t('Continue with {{provider}}', { provider: 'Feishu' })}</span>
										</button>
									{/if}
								</div>
							{/if}

							{#if $config?.features.enable_ldap && $config?.features.enable_login_form}
								<div class="mt-4">
									<button
										class="flex justify-center items-center text-xs w-full text-center text-gray-600 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-400 transition"
										type="button"
										on:click={() => {
											if (mode === 'ldap')
												mode = ($config?.onboarding ?? false) ? 'signup' : 'signin';
											else mode = 'ldap';
										}}
									>
										<span
											>{mode === 'ldap'
												? $i18n.t('Continue with Email')
												: $i18n.t('Continue with LDAP')}</span
										>
									</button>
								</div>
							{/if}
						</div>
						{#if $config?.metadata?.login_footer}
							<div class="max-w-3xl mx-auto mt-6">
								<div class="text-xs text-gray-500 dark:text-gray-400 marked">
									{@html DOMPurify.sanitize(marked($config?.metadata?.login_footer))}
								</div>
							</div>
						{/if}
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	#auth-page {
		background: white;
	}

	:global(.dark) #auth-page {
		background: rgb(3 7 18);
	}

	/* Ensure proper dark mode transitions */
	#auth-container {
		transition: background-color 0.3s ease;
	}

	/* Custom scrollbar for the form area */
	#auth-container::-webkit-scrollbar {
		width: 8px;
	}

	#auth-container::-webkit-scrollbar-track {
		background: transparent;
	}

	#auth-container::-webkit-scrollbar-thumb {
		background: rgba(156, 163, 175, 0.3);
		border-radius: 4px;
	}

	:global(.dark) #auth-container::-webkit-scrollbar-thumb {
		background: rgba(75, 85, 99, 0.5);
	}

	/* Date input styling */
	input[type='date']::-webkit-calendar-picker-indicator {
		filter: invert(0.5);
		cursor: pointer;
	}

	:global(.dark) input[type='date']::-webkit-calendar-picker-indicator {
		filter: invert(0.8);
	}
</style>
