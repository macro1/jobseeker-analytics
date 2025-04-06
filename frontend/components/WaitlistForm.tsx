import { useState } from "react";
import { Button, Card, Input } from "@heroui/react";
import { addToast } from "@heroui/toast";
import { EmailIcon } from "@/components/icons";

const WaitlistForm = () => {
	const [email, setEmail] = useState("");
	const [name, setName] = useState("");
	const [isSubmitting, setIsSubmitting] = useState(false);

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();

		if (!email || !email.includes("@")) {
			addToast({
				title: "Please enter a valid email address",
				color: "danger"
			});
			return;
		}

		setIsSubmitting(true);

		try {
			const response = await fetch("/api/subscribe", {
				method: "POST",
				headers: {
					"Content-Type": "application/json"
				},
				body: JSON.stringify({ email, name, formType: "waitlist" })
			});

			const data = await response.json();

			if (data.success) {
				addToast({
					title: "You've been added to our waitlist!",
					description: "Please check your inbox to confirm your subscription.",
					color: "success"
				});
				setEmail("");
				setName("");
			} else {
				addToast({
					title: "Something went wrong",
					description: data.message || "Please try again later.",
					color: "danger"
				});
			}
		} catch (error) {
			console.error("Error adding to waitlist:", error);
			addToast({
				title: "Connection error",
				description: "Please check your network and try again.",
				color: "danger"
			});
		} finally {
			setIsSubmitting(false);
		}
	};

	return (
		<Card className="p-6 md:p-8">
			<div className="space-y-4">
				<div className="flex items-center gap-2 text-purple-600 font-semibold">
					<span className="bg-purple-100 text-purple-800 p-1 rounded-full">
						<EmailIcon size={16} />
					</span>
					Option 1: Join the Waitlist
				</div>

				<h3 className="text-2xl font-bold">Our beta is full</h3>
				<p className="text-default-500">
					Join our waitlist to receive updates about our launch. Be the first to know when we're live!
				</p>

				<form onSubmit={handleSubmit} className="space-y-4">
					<div>
						<Input
							type="text"
							placeholder="Your name (optional)"
							value={name}
							onChange={(e) => setName(e.target.value)}
							className="mb-2"
						/>
						<div className="relative">
							<Input
								id="email-input"
								type="email"
								placeholder="Your email address"
								value={email}
								onChange={(e) => setEmail(e.target.value)}
								className="mb-2"
								required
							/>
							<Button
								type="submit"
								variant="solid"
								color="primary"
								className="mt-2 bg-purple-600 hover:bg-purple-700 absolute right-0 bottom-0 h-full"
								isDisabled={isSubmitting}
							>
								{isSubmitting ? "Subscribing..." : "Subscribe"}
							</Button>
						</div>
					</div>
					<p className="text-xs text-default-500">
						We'll send updates on our launch. You can unsubscribe anytime.
					</p>
				</form>
			</div>
		</Card>
	);
};

export default WaitlistForm;
