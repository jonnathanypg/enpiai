'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ArrowRight, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { toast } from 'sonner';
import apiClient from '@/lib/api-client';

const evaluationSchema = z.object({
    // Personal
    first_name: z.string().min(2, 'Name is required'),
    email: z.string().email('Valid email required'),
    phone: z.string().min(8, 'Phone required'),
    age: z.string().min(1, 'Age is required'),
    gender: z.enum(['male', 'female', 'other']),
    height_cm: z.string().min(1, 'Height is required'),
    weight_kg: z.string().min(1, 'Weight is required'),

    // Lifestyle
    primary_goal: z.string().min(1, 'Goal is required'),
    activity_level: z.enum(['sedentary', 'light', 'moderate', 'active', 'very_active']),
    meals_per_day: z.string().min(1, 'Required'),
});

type EvaluationFormValues = z.infer<typeof evaluationSchema>;

const STEPS = [
    { id: 'intro', title: 'Start' },
    { id: 'personal', title: 'About You' },
    { id: 'body', title: 'Measurements' },
    { id: 'lifestyle', title: 'Lifestyle' },
    { id: 'contact', title: 'Contact' },
];

export default function EvaluationPage({ params }: { params: { distributor_id: string } }) {
    const [step, setStep] = useState(0);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);

    const {
        register,
        handleSubmit,
        trigger,
        setValue,
        watch,
        formState: { errors },
    } = useForm<EvaluationFormValues>({
        resolver: zodResolver(evaluationSchema),
        mode: 'onChange',
    });

    const nextStep = async () => {
        let fieldsToValidate: any[] = [];
        if (step === 1) fieldsToValidate = ['age', 'gender'];
        if (step === 2) fieldsToValidate = ['height_cm', 'weight_kg'];
        if (step === 3) fieldsToValidate = ['primary_goal', 'activity_level', 'meals_per_day'];

        if (fieldsToValidate.length > 0) {
            const isValid = await trigger(fieldsToValidate);
            if (!isValid) return;
        }
        setStep((s) => s + 1);
    };

    const prevStep = () => setStep((s) => s - 1);

    const onSubmit = async (values: EvaluationFormValues) => {
        setIsSubmitting(true);
        try {
            // Convert numeric strings to numbers for the API
            const payload = {
                ...values,
                age: Number(values.age),
                height_cm: Number(values.height_cm),
                weight_kg: Number(values.weight_kg),
                meals_per_day: Number(values.meals_per_day),
            };
            await apiClient.post(`/wellness/evaluate/${params.distributor_id}`, payload);
            setIsSuccess(true);
        } catch (err) {
            toast.error('Submission failed. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    if (isSuccess) {
        return (
            <div className="flex h-screen items-center justify-center p-4">
                <Card className="max-w-md text-center">
                    <CardHeader>
                        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
                            <CheckCircle2 className="h-8 w-8 text-green-600" />
                        </div>
                        <CardTitle>Evaluation Complete!</CardTitle>
                        <CardDescription>
                            Your wellness profile has been analyzed. We will contact you shortly with your personalized plan.
                        </CardDescription>
                    </CardHeader>
                    <CardFooter className="justify-center">
                        <Button variant="outline" onClick={() => window.location.reload()}>Start New Evaluation</Button>
                    </CardFooter>
                </Card>
            </div>
        );
    }

    const progress = ((step + 1) / STEPS.length) * 100;

    return (
        <div className="mx-auto flex max-w-lg flex-col justify-center px-4 py-12">
            {/* Progress */}
            <div className="mb-8 space-y-2">
                <Progress value={progress} className="h-2" />
                <div className="flex justify-between text-xs text-muted-foreground">
                    <span>Step {step + 1} of {STEPS.length}</span>
                    <span>{STEPS[step].title}</span>
                </div>
            </div>

            <Card>
                <form onSubmit={handleSubmit(onSubmit)}>
                    {/* Step 0: Intro */}
                    {step === 0 && (
                        <>
                            <CardHeader>
                                <CardTitle className="text-2xl">Free Wellness Check</CardTitle>
                                <CardDescription>
                                    Get a personalized health analysis and nutrition plan in under 2 minutes.
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-4">
                                    <ul className="space-y-2 text-sm">
                                        <li className="flex items-center gap-2">🔹 Body Mass Index (BMI) Calculation</li>
                                        <li className="flex items-center gap-2">🔹 Personalized Protein Factor</li>
                                        <li className="flex items-center gap-2">🔹 Custom Meal Plan Suggestions</li>
                                    </ul>
                                </div>
                            </CardContent>
                            <CardFooter>
                                <Button type="button" onClick={() => setStep(1)} className="w-full">
                                    Start Now <ArrowRight className="ml-2 h-4 w-4" />
                                </Button>
                            </CardFooter>
                        </>
                    )}

                    {/* Step 1: Personal */}
                    {step === 1 && (
                        <>
                            <CardHeader><CardTitle>About You</CardTitle></CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <Label>Age</Label>
                                    <Input type="number" {...register('age')} placeholder="e.g. 30" />
                                    {errors.age && <p className="text-xs text-destructive">{errors.age.message}</p>}
                                </div>
                                <div className="space-y-2">
                                    <Label>Gender</Label>
                                    <RadioGroup onValueChange={(v) => setValue('gender', v as any)} defaultValue={watch('gender')}>
                                        <div className="flex items-center space-x-2">
                                            <RadioGroupItem value="female" id="r1" />
                                            <Label htmlFor="r1">Female</Label>
                                        </div>
                                        <div className="flex items-center space-x-2">
                                            <RadioGroupItem value="male" id="r2" />
                                            <Label htmlFor="r2">Male</Label>
                                        </div>
                                    </RadioGroup>
                                    {errors.gender && <p className="text-xs text-destructive">{errors.gender.message}</p>}
                                </div>
                            </CardContent>
                            <CardFooter className="flex justify-between">
                                <Button type="button" variant="outline" onClick={prevStep}>Back</Button>
                                <Button type="button" onClick={nextStep}>Next <ArrowRight className="ml-2 h-4 w-4" /></Button>
                            </CardFooter>
                        </>
                    )}

                    {/* Step 2: Body */}
                    {step === 2 && (
                        <>
                            <CardHeader><CardTitle>Measurements</CardTitle></CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label>Height (cm)</Label>
                                        <Input type="number" {...register('height_cm')} placeholder="170" />
                                        {errors.height_cm && <p className="text-xs text-destructive">{errors.height_cm.message}</p>}
                                    </div>
                                    <div className="space-y-2">
                                        <Label>Weight (kg)</Label>
                                        <Input type="number" {...register('weight_kg')} placeholder="70" />
                                        {errors.weight_kg && <p className="text-xs text-destructive">{errors.weight_kg.message}</p>}
                                    </div>
                                </div>
                            </CardContent>
                            <CardFooter className="flex justify-between">
                                <Button type="button" variant="outline" onClick={prevStep}>Back</Button>
                                <Button type="button" onClick={nextStep}>Next <ArrowRight className="ml-2 h-4 w-4" /></Button>
                            </CardFooter>
                        </>
                    )}

                    {/* Step 3: Lifestyle */}
                    {step === 3 && (
                        <>
                            <CardHeader><CardTitle>Lifestyle & Goals</CardTitle></CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <Label>Primary Goal</Label>
                                    <Input {...register('primary_goal')} placeholder="e.g. Lose weight, Gain muscle" />
                                    {errors.primary_goal && <p className="text-xs text-destructive">{errors.primary_goal.message}</p>}
                                </div>
                                <div className="space-y-2">
                                    <Label>Activity Level</Label>
                                    <select
                                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                                        {...register('activity_level')}
                                    >
                                        <option value="sedentary">Sedentary (Little or no exercise)</option>
                                        <option value="light">Light (Exercise 1-3 times/week)</option>
                                        <option value="moderate">Moderate (Exercise 4-5 times/week)</option>
                                        <option value="active">Active (Daily exercise)</option>
                                        <option value="very_active">Very Active (Intense exercise)</option>
                                    </select>
                                </div>
                                <div className="space-y-2">
                                    <Label>Meals per Day</Label>
                                    <Input type="number" {...register('meals_per_day')} placeholder="3" />
                                    {errors.meals_per_day && <p className="text-xs text-destructive">{errors.meals_per_day.message}</p>}
                                </div>
                            </CardContent>
                            <CardFooter className="flex justify-between">
                                <Button type="button" variant="outline" onClick={prevStep}>Back</Button>
                                <Button type="button" onClick={nextStep}>Next <ArrowRight className="ml-2 h-4 w-4" /></Button>
                            </CardFooter>
                        </>
                    )}

                    {/* Step 4: Contact */}
                    {step === 4 && (
                        <>
                            <CardHeader><CardTitle>Almost Done!</CardTitle><CardDescription>Where should we send your results?</CardDescription></CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <Label>First Name</Label>
                                    <Input {...register('first_name')} placeholder="Jane" />
                                    {errors.first_name && <p className="text-xs text-destructive">{errors.first_name.message}</p>}
                                </div>
                                <div className="space-y-2">
                                    <Label>Email</Label>
                                    <Input type="email" {...register('email')} placeholder="jane@example.com" />
                                    {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
                                </div>
                                <div className="space-y-2">
                                    <Label>Phone (WhatsApp)</Label>
                                    <Input type="tel" {...register('phone')} placeholder="+1 234 567 8900" />
                                    {errors.phone && <p className="text-xs text-destructive">{errors.phone.message}</p>}
                                </div>
                            </CardContent>
                            <CardFooter className="flex justify-between">
                                <Button type="button" variant="outline" onClick={prevStep}>Back</Button>
                                <Button type="submit" disabled={isSubmitting}>
                                    {isSubmitting ? 'Analyzing...' : 'Get My Results'}
                                </Button>
                            </CardFooter>
                        </>
                    )}
                </form>
            </Card>
        </div>
    );
}
