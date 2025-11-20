"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { authService } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { User, Mail, Lock, CheckCircle2 } from "lucide-react";

export default function ProfileSettingsPage() {
  const queryClient = useQueryClient();
  const [passwordData, setPasswordData] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [emailData, setEmailData] = useState({
    new_email: "",
    password: "",
  });
  const [passwordError, setPasswordError] = useState("");
  const [emailError, setEmailError] = useState("");
  const [passwordSuccess, setPasswordSuccess] = useState(false);
  const [emailSuccess, setEmailSuccess] = useState(false);
  const [emailSuccessMessage, setEmailSuccessMessage] = useState("");

  // Fetch current user
  const { data: user, refetch: refetchUser } = useQuery({
    queryKey: ["currentUser"],
    queryFn: () => authService.getCurrentUser(),
  });

  // Change password mutation
  const changePasswordMutation = useMutation({
    mutationFn: (data: { current_password: string; new_password: string }) =>
      authService.changePassword(data),
    onSuccess: () => {
      setPasswordError("");
      setPasswordSuccess(true);
      setPasswordData({ current_password: "", new_password: "", confirm_password: "" });
      setTimeout(() => setPasswordSuccess(false), 5000);
    },
    onError: (error: any) => {
      setPasswordSuccess(false);
      setPasswordError(error.message || "Failed to change password");
    },
  });

  // Change email mutation
  const changeEmailMutation = useMutation({
    mutationFn: (data: { new_email: string; password: string }) =>
      authService.changeEmail(data),
    onSuccess: (data: any) => {
      setEmailError("");
      setEmailSuccess(true);
      // Store the backend message to display to user
      setEmailSuccessMessage(data?.message || "Email changed successfully");
      setEmailData({ new_email: "", password: "" });
      refetchUser(); // Refresh user data
      // Invalidate recipients query to refresh the list in Settings page
      queryClient.invalidateQueries({ queryKey: ["recipients"] });
      setTimeout(() => {
        setEmailSuccess(false);
        setEmailSuccessMessage("");
      }, 5000);
    },
    onError: (error: any) => {
      setEmailSuccess(false);
      setEmailError(error.message || "Failed to change email");
    },
  });

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError("");
    setPasswordSuccess(false);

    // Validate
    if (passwordData.new_password.length < 6) {
      setPasswordError("New password must be at least 6 characters");
      return;
    }

    if (passwordData.new_password !== passwordData.confirm_password) {
      setPasswordError("Passwords do not match");
      return;
    }

    if (passwordData.new_password === passwordData.current_password) {
      setPasswordError("New password must be different from current password");
      return;
    }

    changePasswordMutation.mutate({
      current_password: passwordData.current_password,
      new_password: passwordData.new_password,
    });
  };

  const handleEmailSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setEmailError("");
    setEmailSuccess(false);

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(emailData.new_email)) {
      setEmailError("Please enter a valid email address");
      return;
    }

    if (emailData.new_email === user?.email) {
      setEmailError("New email must be different from current email");
      return;
    }

    changeEmailMutation.mutate(emailData);
  };

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Profile Settings</h1>
        <p className="text-muted-foreground mt-2">
          Manage your account settings and preferences
        </p>
      </div>

      {/* User Info Card */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Account Information
          </CardTitle>
          <CardDescription>Your current account details</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <Label className="text-sm text-muted-foreground">Username</Label>
            <p className="text-base font-medium">{user?.username}</p>
          </div>
          <div>
            <Label className="text-sm text-muted-foreground">Email</Label>
            <p className="text-base font-medium">{user?.email}</p>
          </div>
          <div>
            <Label className="text-sm text-muted-foreground">Role</Label>
            <p className="text-base font-medium">
              {user?.is_admin ? "Administrator" : "User"}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Change Password Card */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lock className="h-5 w-5" />
            Change Password
          </CardTitle>
          <CardDescription>Update your password to keep your account secure</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            {passwordError && (
              <Alert variant="destructive">
                <AlertDescription>{passwordError}</AlertDescription>
              </Alert>
            )}

            {passwordSuccess && (
              <Alert className="bg-green-50 text-green-900 border-green-200">
                <CheckCircle2 className="h-4 w-4" />
                <AlertDescription>Password changed successfully!</AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="current_password">Current Password</Label>
              <Input
                id="current_password"
                type="password"
                value={passwordData.current_password}
                onChange={(e) =>
                  setPasswordData({ ...passwordData, current_password: e.target.value })
                }
                required
                disabled={changePasswordMutation.isPending}
              />
            </div>

            <Separator />

            <div className="space-y-2">
              <Label htmlFor="new_password">New Password</Label>
              <Input
                id="new_password"
                type="password"
                value={passwordData.new_password}
                onChange={(e) =>
                  setPasswordData({ ...passwordData, new_password: e.target.value })
                }
                required
                minLength={6}
                disabled={changePasswordMutation.isPending}
              />
              <p className="text-xs text-muted-foreground">
                Must be at least 6 characters
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirm_password">Confirm New Password</Label>
              <Input
                id="confirm_password"
                type="password"
                value={passwordData.confirm_password}
                onChange={(e) =>
                  setPasswordData({ ...passwordData, confirm_password: e.target.value })
                }
                required
                disabled={changePasswordMutation.isPending}
              />
            </div>

            <Button
              type="submit"
              disabled={changePasswordMutation.isPending}
              className="w-full sm:w-auto"
            >
              {changePasswordMutation.isPending ? "Changing..." : "Change Password"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Change Email Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5" />
            Change Email Address
          </CardTitle>
          <CardDescription>
            Update your email address for notifications and account recovery
            {user?.is_admin && (
              <span className="block mt-1 text-amber-600">
                Note: As an admin, this will also update your alert notification email
              </span>
            )}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleEmailSubmit} className="space-y-4">
            {emailError && (
              <Alert variant="destructive">
                <AlertDescription>{emailError}</AlertDescription>
              </Alert>
            )}

            {emailSuccess && (
              <Alert className="bg-green-50 text-green-900 border-green-200">
                <CheckCircle2 className="h-4 w-4" />
                <AlertDescription>
                  {emailSuccessMessage}
                </AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="current_email">Current Email</Label>
              <Input
                id="current_email"
                type="email"
                value={user?.email || ""}
                disabled
                className="bg-muted"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="new_email">New Email Address</Label>
              <Input
                id="new_email"
                type="email"
                value={emailData.new_email}
                onChange={(e) =>
                  setEmailData({ ...emailData, new_email: e.target.value })
                }
                required
                disabled={changeEmailMutation.isPending}
              />
            </div>

            <Separator />

            <div className="space-y-2">
              <Label htmlFor="email_password">Confirm Password</Label>
              <Input
                id="email_password"
                type="password"
                value={emailData.password}
                onChange={(e) =>
                  setEmailData({ ...emailData, password: e.target.value })
                }
                required
                disabled={changeEmailMutation.isPending}
              />
              <p className="text-xs text-muted-foreground">
                Enter your current password to confirm this change
              </p>
            </div>

            <Button
              type="submit"
              disabled={changeEmailMutation.isPending}
              className="w-full sm:w-auto"
            >
              {changeEmailMutation.isPending ? "Changing..." : "Change Email"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
