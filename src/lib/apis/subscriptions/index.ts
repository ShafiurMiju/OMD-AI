import { WEBUI_API_BASE_URL } from '$lib/constants';

export const getSubscriptionPlans = async (token: string = '') => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/subscriptions/plans`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			...(token && { Authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getPlanById = async (token: string, planId: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/subscriptions/plans/${planId}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const createSubscription = async (
	token: string,
	planId: string,
	paymentId: string | null = null,
	paymentMethod: string = 'stripe'
) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/subscriptions/user/subscription`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			plan_id: planId,
			payment_id: paymentId,
			payment_method: paymentMethod
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getUserSubscription = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/subscriptions/user/subscription`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const verifyPayment = async (
	paymentId: string,
	subscriptionId: string,
	paymentMethod: string = 'stripe'
) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/subscriptions/verify-payment`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			payment_id: paymentId,
			subscription_id: subscriptionId,
			payment_method: paymentMethod
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// Admin endpoints
export const createPlan = async (
	token: string,
	plan: {
		plan_name: string;
		subtitle?: string;
		plan_type?: string;
		duration_type?: string;
		plan_duration?: number;
		price: number;
		benefits?: string[];
		additional_info?: string;
		group?: string;
	}
) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/subscriptions/plans`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(plan)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const updatePlan = async (token: string, planId: string, updates: any) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/subscriptions/plans/${planId}`, {
		method: 'PATCH',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(updates)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const deletePlan = async (token: string, planId: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/subscriptions/plans/${planId}`, {
		method: 'DELETE',
		headers: {
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};
