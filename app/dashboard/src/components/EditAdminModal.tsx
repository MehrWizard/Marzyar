import {
  Badge,
  Box,
  Button,
  chakra,
  Checkbox,
  Collapse,
  Divider,
  FormControl,
  FormLabel,
  HStack,
  IconButton,
  Input as ChakraInput,
  InputGroup,
  InputRightElement,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Progress,
  Select,
  SimpleGrid,
  Switch,
  Text,
  Tooltip,
  useToast,
  VStack,
} from "@chakra-ui/react";
import {
  AdjustmentsHorizontalIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  EyeIcon,
  EyeSlashIcon,
  LockClosedIcon,
  NoSymbolIcon,
  PencilSquareIcon,
  TrashIcon,
} from "@heroicons/react/24/outline";
import { zodResolver } from "@hookform/resolvers/zod";
import { FetchAdminsQueryKey, useAdmins } from "contexts/AdminsContext";
import { useDashboard } from "contexts/DashboardContext";
import { FetchMarzyarAdminsQueryKey, useMarzyar } from "contexts/MarzyarContext";
import useGetUser from "hooks/useGetUser";
import { FC, useEffect, useMemo, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { useMutation, useQueryClient } from "react-query";
import { AdminModify, AdminModifySchema } from "types/Admin";
import { formatBytes } from "utils/formatByte";
import { generateErrorMessage, generateSuccessMessage } from "utils/toastHandler";
import { Icon } from "./Icon";
import { Input } from "./Input";

const CustomInput = chakra(Input, {
  baseStyle: {
    bg: "white",
    _dark: {
      bg: "gray.700",
    },
  },
});

const ModalIcon = chakra(PencilSquareIcon, {
  baseStyle: {
    w: 5,
    h: 5,
  },
});

export const EditAdminModal: FC = () => {
  const {
    editingAdmin,
    setEditingAdmin,
    modifyAdmin,
    setDeletingAdmin,
    resetAdminUsage,
    disableAdminUsers,
    activateAdminUsers,
  } = useAdmins();
  const { inbounds } = useDashboard();
  const { t } = useTranslation();
  const toast = useToast();
  const queryClient = useQueryClient();
  const { userData } = useGetUser();

  const [showPassword, setShowPassword] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Marzyar Reseller state
  const [usersLimit, setUsersLimit] = useState<string>("");
  const [trafficLimit, setTrafficLimit] = useState<string>("");
  const [trafficLimitUnit, setTrafficLimitUnit] = useState<"GB" | "TB">("GB");
  const [oversellAllowed, setOversellAllowed] = useState<boolean>(false);
  const [allowedInbounds, setAllowedInbounds] = useState<string[]>([]);

  const isCurrentAdmin = userData?.username === editingAdmin?.username;
  const isAnotherSudo = !isCurrentAdmin && !!editingAdmin?.is_sudo;

  // Retrieve current Marzyar settings for this admin
  const adminSettings = useMarzyar((s) =>
    editingAdmin ? s.adminSettingsByUsername[editingAdmin.username] : undefined
  );

  const form = useForm<AdminModify>({
    resolver: zodResolver(AdminModifySchema),
    defaultValues: {
      password: "",
      is_sudo: editingAdmin?.is_sudo ?? false,
      telegram_id: editingAdmin?.telegram_id ?? null,
      discord_webhook: editingAdmin?.discord_webhook ?? "",
    },
  });

  const isSudoValue = form.watch("is_sudo");

  // Extract available system inbounds
  const availableInbounds = useMemo(() => {
    const tags: string[] = [];
    if (inbounds instanceof Map) {
      inbounds.forEach((items) => {
        if (Array.isArray(items)) {
          items.forEach((i: any) => {
            if (i?.tag && !tags.includes(i.tag)) tags.push(i.tag);
          });
        }
      });
    } else if (inbounds && typeof inbounds === "object") {
      Object.values(inbounds).forEach((items: any) => {
        if (Array.isArray(items)) {
          items.forEach((i: any) => {
            if (i?.tag && !tags.includes(i.tag)) tags.push(i.tag);
          });
        }
      });
    }
    return tags;
  }, [inbounds]);

  useEffect(() => {
    if (editingAdmin) {
      form.reset({
        password: "",
        is_sudo: editingAdmin.is_sudo,
        telegram_id: editingAdmin.telegram_id ?? null,
        discord_webhook: editingAdmin.discord_webhook ?? "",
      });

      if (adminSettings) {
        setUsersLimit(
          adminSettings.users_limit !== null ? String(adminSettings.users_limit) : ""
        );
        if (adminSettings.traffic_limit !== null) {
          const tbThreshold = 1099511627776;
          if (
            adminSettings.traffic_limit >= tbThreshold &&
            adminSettings.traffic_limit % tbThreshold === 0
          ) {
            setTrafficLimit(String(adminSettings.traffic_limit / tbThreshold));
            setTrafficLimitUnit("TB");
          } else {
            setTrafficLimit(
              String(Math.round((adminSettings.traffic_limit / 1073741824) * 100) / 100)
            );
            setTrafficLimitUnit("GB");
          }
        } else {
          setTrafficLimit("");
          setTrafficLimitUnit("GB");
        }
        setOversellAllowed(adminSettings.oversell_allowed);
        setAllowedInbounds(adminSettings.allowed_inbounds || []);
      } else {
        setUsersLimit("");
        setTrafficLimit("");
        setTrafficLimitUnit("GB");
        setOversellAllowed(false);
        setAllowedInbounds([]);
      }
    }
  }, [editingAdmin, adminSettings, form]);

  const onClose = () => {
    form.reset();
    setEditingAdmin(null);
  };

  const { isLoading: isUpdating, mutate: onUpdate } = useMutation(
    async (data: AdminModify) => {
      if (!editingAdmin) throw new Error("No admin selected");
      const updated = await modifyAdmin(editingAdmin.username, data);

      // If non-sudo, update Marzyar limits
      if (!data.is_sudo) {
        const uLimit = usersLimit.trim() ? parseInt(usersLimit) : null;
        let tLimit: number | null = null;
        if (trafficLimit.trim() && Number(trafficLimit) > 0) {
          const mult = trafficLimitUnit === "TB" ? 1099511627776 : 1073741824;
          tLimit = Math.round(Number(trafficLimit) * mult);
        }
        const inboundsPayload = allowedInbounds.length > 0 ? allowedInbounds : null;

        await useMarzyar.getState().updateAdminSettings(editingAdmin.username, {
          users_limit: uLimit,
          traffic_limit: tLimit,
          oversell_allowed: oversellAllowed,
          allowed_inbounds: inboundsPayload,
        });
      }

      return updated;
    },
    {
      onSuccess: () => {
        generateSuccessMessage(
          t("admins.editAdminSuccess", { username: editingAdmin?.username }),
          toast
        );
        form.setValue("password", "");
        queryClient.invalidateQueries(FetchAdminsQueryKey);
        queryClient.invalidateQueries(FetchMarzyarAdminsQueryKey);
        useDashboard.getState().refetchUsers();
        onClose();
      },
      onError: (e) => {
        generateErrorMessage(e, toast, form);
      },
    }
  );

  if (!editingAdmin) return null;

  const handleResetUsage = async () => {
    if (
      !window.confirm(
        t("admins.resetUsageConfirm", { username: editingAdmin.username })
      )
    )
      return;
    setActionLoading("resetUsage");
    try {
      await resetAdminUsage(editingAdmin.username);
      generateSuccessMessage(
        t("admins.resetUsageSuccess", { username: editingAdmin.username }),
        toast
      );
      queryClient.invalidateQueries(FetchAdminsQueryKey);
    } catch (e) {
      generateErrorMessage(e, toast);
    } finally {
      setActionLoading(null);
    }
  };

  const handleResetQuota = async () => {
    if (!editingAdmin) return;
    if (
      !window.confirm(
        t("marzyar.resetQuotaConfirm", {
          username: editingAdmin.username,
          defaultValue: `Are you sure you want to reset consumed quota for ${editingAdmin.username}? All locked users will be unlocked.`,
        })
      )
    )
      return;
    setActionLoading("resetQuota");
    try {
      await useMarzyar.getState().resetAdminQuota(editingAdmin.username);
      generateSuccessMessage(
        t("marzyar.resetQuotaSuccess", {
          username: editingAdmin.username,
          defaultValue: `Quota reset and users unlocked for ${editingAdmin.username}`,
        }),
        toast
      );
      queryClient.invalidateQueries(FetchMarzyarAdminsQueryKey);
      queryClient.invalidateQueries(FetchAdminsQueryKey);
      useDashboard.getState().refetchUsers();
    } catch (e) {
      generateErrorMessage(e, toast);
    } finally {
      setActionLoading(null);
    }
  };

  const handleDisableUsers = async () => {
    if (
      !window.confirm(
        t("admins.disableUsersConfirm", { username: editingAdmin.username })
      )
    )
      return;
    setActionLoading("disableUsers");
    try {
      await disableAdminUsers(editingAdmin.username);
      generateSuccessMessage(
        t("admins.disableUsersSuccess", { username: editingAdmin.username }),
        toast
      );
      useDashboard.getState().refetchUsers();
      queryClient.invalidateQueries(FetchAdminsQueryKey);
    } catch (e) {
      generateErrorMessage(e, toast);
    } finally {
      setActionLoading(null);
    }
  };

  const handleActivateUsers = async () => {
    if (
      !window.confirm(
        t("admins.activateUsersConfirm", { username: editingAdmin.username })
      )
    )
      return;
    setActionLoading("activateUsers");
    try {
      await activateAdminUsers(editingAdmin.username);
      generateSuccessMessage(
        t("admins.activateUsersSuccess", { username: editingAdmin.username }),
        toast
      );
      useDashboard.getState().refetchUsers();
      queryClient.invalidateQueries(FetchAdminsQueryKey);
    } catch (e) {
      generateErrorMessage(e, toast);
    } finally {
      setActionLoading(null);
    }
  };

  const toggleInbound = (tag: string) => {
    setAllowedInbounds((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  const handleSelectAllInbounds = () => {
    if (allowedInbounds.length === availableInbounds.length) {
      setAllowedInbounds([]);
    } else {
      setAllowedInbounds([...availableInbounds]);
    }
  };

  // Quota calculation percentages
  const quotaPercent =
    adminSettings?.traffic_limit && adminSettings.traffic_limit > 0
      ? Math.min(
          100,
          Math.round(
            ((adminSettings.oversell_allowed
              ? adminSettings.current_consumed_traffic
              : adminSettings.current_allocated_traffic) /
              adminSettings.traffic_limit) *
              100
          )
        )
      : null;

  return (
    <Modal isOpen={!!editingAdmin} onClose={onClose} isCentered size="lg">
      <ModalOverlay bg="blackAlpha.400" backdropFilter="blur(8px)" />
      <ModalContent mx={3} maxH="90vh" overflowY="auto">
        <ModalHeader display="flex" alignItems="center" gap={3} pt={5}>
          <Icon color="primary">
            <ModalIcon color="white" />
          </Icon>
          <Box>
            <HStack spacing={2} align="center">
              <Text fontSize="lg" fontWeight="semibold">
                {editingAdmin.username}
              </Text>
              {isCurrentAdmin && (
                <Badge colorScheme="green" variant="subtle" fontSize="2xs">
                  {t("admins.you")}
                </Badge>
              )}
              <Badge
                colorScheme={editingAdmin.is_sudo ? "purple" : "blue"}
                rounded="full"
                px={2}
                fontSize="2xs"
              >
                {editingAdmin.is_sudo ? t("admins.sudo") : t("admins.regular")}
              </Badge>
            </HStack>
            <Text fontSize="xs" color="gray.500" fontWeight="normal">
              {t("admins.usersUsage")}: {formatBytes(editingAdmin.users_usage || 0)}
              {editingAdmin.users_count !== undefined && (
                <> • {editingAdmin.users_count} {t("users")}</>
              )}
            </Text>
          </Box>
        </ModalHeader>
        <ModalCloseButton mt={3} />

        {isAnotherSudo ? (
          <ModalBody py={6}>
            <VStack spacing={4} align="stretch">
              <Text fontSize="sm" color="gray.500">
                {t("admins.cannotEditOtherSudo")}
              </Text>
              <Divider borderColor="light-border" _dark={{ borderColor: "gray.700" }} />
              <HStack justify="space-between" spacing={2}>
                <Button
                  size="sm"
                  variant="outline"
                  colorScheme="orange"
                  onClick={handleResetUsage}
                  isLoading={actionLoading === "resetUsage"}
                  leftIcon={<ArrowPathIcon width="16px" />}
                >
                  {t("admins.resetUsage")}
                </Button>
                <HStack spacing={2}>
                  <Button
                    size="sm"
                    variant="outline"
                    colorScheme="red"
                    onClick={handleDisableUsers}
                    isLoading={actionLoading === "disableUsers"}
                    leftIcon={<NoSymbolIcon width="16px" />}
                  >
                    {t("admins.disableUsers")}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    colorScheme="green"
                    onClick={handleActivateUsers}
                    isLoading={actionLoading === "activateUsers"}
                    leftIcon={<CheckCircleIcon width="16px" />}
                  >
                    {t("admins.activateUsers")}
                  </Button>
                </HStack>
              </HStack>
            </VStack>
          </ModalBody>
        ) : (
          <form onSubmit={form.handleSubmit((data) => onUpdate(data))}>
            <ModalBody py={4}>
              <VStack spacing={4} align="stretch">
                {/* Live Quota Status Banner if Quota Exceeded or Users Locked */}
                {adminSettings && adminSettings.locked_users_count > 0 && (
                  <Box
                    p={3}
                    borderRadius="lg"
                    bg="red.50"
                    _dark={{ bg: "red.900", color: "red.100" }}
                    borderWidth="1px"
                    borderColor="red.300"
                  >
                    <HStack justify="space-between" align="center">
                      <HStack spacing={2}>
                        <LockClosedIcon width="20px" height="20px" color="currentColor" />
                        <VStack align="flex-start" spacing={0}>
                          <Text fontSize="xs" fontWeight="bold">
                            {t("marzyar.quotaExceeded", "Quota Exceeded")}
                          </Text>
                          <Text fontSize="2xs">
                            {t("marzyar.usersLocked", {
                              count: adminSettings.locked_users_count,
                              defaultValue: `${adminSettings.locked_users_count} users locked and disconnected from proxy.`,
                            })}
                          </Text>
                        </VStack>
                      </HStack>
                      <Button
                        size="xs"
                        colorScheme="red"
                        variant="solid"
                        onClick={handleResetQuota}
                        isLoading={actionLoading === "resetQuota"}
                      >
                        {t("marzyar.resetQuota", "Reset Quota")}
                      </Button>
                    </HStack>
                  </Box>
                )}

                {/* Quota & Usage Progress Card if reseller limits exist */}
                {adminSettings &&
                  (adminSettings.traffic_limit !== null || adminSettings.users_limit !== null) && (
                    <Box
                      p={3}
                      borderRadius="lg"
                      borderWidth="1px"
                      borderColor="light-border"
                      _dark={{ borderColor: "gray.700", bg: "whiteAlpha.50" }}
                    >
                      <VStack spacing={2} align="stretch">
                        {adminSettings.traffic_limit !== null && (
                          <Box>
                            <HStack justify="space-between" fontSize="xs" mb={1}>
                              <Text color="gray.500">
                                {t("marzyar.trafficQuota", "Traffic Quota")} (
                                {adminSettings.oversell_allowed
                                  ? t("marzyar.oversellConsumed", "Consumed")
                                  : t("marzyar.allocatedLimit", "Allocated")}
                                ):
                              </Text>
                              <Text fontWeight="semibold">
                                {formatBytes(
                                  adminSettings.oversell_allowed
                                    ? adminSettings.current_consumed_traffic
                                    : adminSettings.current_allocated_traffic
                                )}{" "}
                                / {formatBytes(adminSettings.traffic_limit)}
                              </Text>
                            </HStack>
                            <Progress
                              value={quotaPercent || 0}
                              size="xs"
                              colorScheme={
                                (quotaPercent || 0) >= 100
                                  ? "red"
                                  : (quotaPercent || 0) >= 80
                                  ? "orange"
                                  : "blue"
                              }
                              borderRadius="full"
                            />
                          </Box>
                        )}

                        {adminSettings.users_limit !== null && (
                          <HStack justify="space-between" fontSize="xs">
                            <Text color="gray.500">{t("marzyar.usersLimit", "User Slots")}:</Text>
                            <Text fontWeight="semibold">
                              {adminSettings.current_users_count} / {adminSettings.users_limit}{" "}
                              {adminSettings.is_user_limit_exceeded && (
                                <Badge colorScheme="red" fontSize="2xs" ml={1}>
                                  {t("marzyar.limitReached", "Limit Reached")}
                                </Badge>
                              )}
                            </Text>
                          </HStack>
                        )}
                      </VStack>
                    </Box>
                  )}

                <FormControl>
                  <FormLabel fontSize="xs" mb={1} color="gray.600" _dark={{ color: "gray.400" }}>
                    {t("admins.newPassword")}
                  </FormLabel>
                  <InputGroup size="md">
                    <ChakraInput
                      type={showPassword ? "text" : "password"}
                      placeholder={t("admins.newPasswordPlaceholder")}
                      bg="white"
                      _dark={{ bg: "gray.700" }}
                      borderRadius="md"
                      {...form.register("password")}
                    />
                    <InputRightElement>
                      <IconButton
                        size="sm"
                        variant="ghost"
                        aria-label="Toggle password visibility"
                        icon={showPassword ? <EyeSlashIcon width="18px" /> : <EyeIcon width="18px" />}
                        onClick={() => setShowPassword(!showPassword)}
                      />
                    </InputRightElement>
                  </InputGroup>
                </FormControl>

                <HStack
                  justify="space-between"
                  p={3}
                  borderRadius="lg"
                  borderWidth="1px"
                  borderColor="light-border"
                  _dark={{ borderColor: "gray.700", bg: "whiteAlpha.50" }}
                >
                  <VStack align="flex-start" spacing={0}>
                    <FormLabel fontSize="sm" m={0} fontWeight="medium">
                      {t("admins.sudo")}
                    </FormLabel>
                    <Text fontSize="xs" color="gray.500">
                      {t("admins.sudoHelp")}
                    </Text>
                  </VStack>
                  <Controller
                    name="is_sudo"
                    control={form.control}
                    render={({ field }) => (
                      <Switch
                        colorScheme="primary"
                        isChecked={field.value}
                        onChange={(e) => field.onChange(e.target.checked)}
                        isDisabled={isCurrentAdmin}
                      />
                    )}
                  />
                </HStack>

                <HStack spacing={3} align="flex-start">
                  <Box flex="1">
                    <CustomInput
                      label={t("admins.telegramId")}
                      placeholder="123456789"
                      type="number"
                      {...form.register("telegram_id")}
                      error={form.formState?.errors?.telegram_id?.message}
                    />
                  </Box>
                  <Box flex="1">
                    <CustomInput
                      label={t("admins.discordWebhook")}
                      placeholder="https://discord.com/api/webhooks/..."
                      {...form.register("discord_webhook")}
                      error={form.formState?.errors?.discord_webhook?.message}
                    />
                  </Box>
                </HStack>

                {/* Reseller Limits & Quota Section (Only for Regular Admins) */}
                <Collapse in={!isSudoValue} animateOpacity>
                  <Box
                    p={4}
                    borderRadius="xl"
                    borderWidth="1px"
                    borderColor="light-border"
                    _dark={{ borderColor: "gray.700", bg: "whiteAlpha.50" }}
                    bg="blackAlpha.50"
                    mt={2}
                  >
                    <HStack justify="space-between" mb={3}>
                      <HStack spacing={2}>
                        <AdjustmentsHorizontalIcon width="18px" height="18px" />
                        <Text fontSize="sm" fontWeight="bold">
                          {t("marzyar.resellerLimits", "Reseller Limits & Quota")}
                        </Text>
                        <Badge colorScheme="blue" fontSize="2xs">
                          Marzyar
                        </Badge>
                      </HStack>

                      {adminSettings?.traffic_limit !== null && (
                        <Button
                          size="xs"
                          variant="ghost"
                          colorScheme="orange"
                          leftIcon={<ArrowPathIcon width="14px" />}
                          onClick={handleResetQuota}
                          isLoading={actionLoading === "resetQuota"}
                        >
                          {t("marzyar.resetQuota", "Reset Quota")}
                        </Button>
                      )}
                    </HStack>

                    <VStack spacing={4} align="stretch">
                      <HStack spacing={3} align="flex-end">
                        <Box flex="1">
                          <FormControl>
                            <FormLabel fontSize="xs" mb={1} color="gray.600" _dark={{ color: "gray.400" }}>
                              {t("marzyar.usersLimit", "User Accounts Limit")}
                            </FormLabel>
                            <ChakraInput
                              type="number"
                              placeholder={t("unlimited", "Unlimited")}
                              value={usersLimit}
                              onChange={(e) => setUsersLimit(e.target.value)}
                              bg="white"
                              _dark={{ bg: "gray.700" }}
                              size="sm"
                              rounded="md"
                            />
                          </FormControl>
                        </Box>

                        <Box flex="1.4">
                          <FormControl>
                            <FormLabel fontSize="xs" mb={1} color="gray.600" _dark={{ color: "gray.400" }}>
                              {t("marzyar.trafficLimit", "Traffic Quota")}
                            </FormLabel>
                            <HStack spacing={1}>
                              <ChakraInput
                                type="number"
                                placeholder={t("unlimited", "Unlimited")}
                                value={trafficLimit}
                                onChange={(e) => setTrafficLimit(e.target.value)}
                                bg="white"
                                _dark={{ bg: "gray.700" }}
                                size="sm"
                                rounded="md"
                              />
                              <Select
                                w="75px"
                                size="sm"
                                value={trafficLimitUnit}
                                onChange={(e) => setTrafficLimitUnit(e.target.value as "GB" | "TB")}
                                bg="white"
                                _dark={{ bg: "gray.700" }}
                                rounded="md"
                              >
                                <option value="GB">GB</option>
                                <option value="TB">TB</option>
                              </Select>
                            </HStack>
                          </FormControl>
                        </Box>
                      </HStack>

                      <HStack
                        justify="space-between"
                        p={3}
                        borderRadius="lg"
                        borderWidth="1px"
                        borderColor="light-border"
                        _dark={{ borderColor: "gray.600", bg: "blackAlpha.200" }}
                        bg="white"
                      >
                        <VStack align="flex-start" spacing={0}>
                          <FormLabel fontSize="xs" m={0} fontWeight="medium">
                            {t("marzyar.oversellAllowed", "Allow Overselling")}
                          </FormLabel>
                          <Text fontSize="2xs" color="gray.500">
                            {oversellAllowed
                              ? t(
                                  "marzyar.oversellOnHelp",
                                  "Quota restricts actual traffic consumed. Users can be given higher limits."
                                )
                              : t(
                                  "marzyar.oversellOffHelp",
                                  "Quota restricts total allocated user limits. Sum of user limits cannot exceed quota."
                                )}
                          </Text>
                        </VStack>
                        <Switch
                          colorScheme="primary"
                          isChecked={oversellAllowed}
                          onChange={(e) => setOversellAllowed(e.target.checked)}
                        />
                      </HStack>

                      {/* Allowed Inbounds Selector */}
                      {availableInbounds.length > 0 && (
                        <Box>
                          <HStack justify="space-between" mb={1.5}>
                            <FormLabel fontSize="xs" m={0} color="gray.600" _dark={{ color: "gray.400" }}>
                              {t("marzyar.allowedInbounds", "Allowed Inbounds")}
                            </FormLabel>
                            <Button
                              size="2xs"
                              variant="link"
                              colorScheme="primary"
                              onClick={handleSelectAllInbounds}
                            >
                              {allowedInbounds.length === availableInbounds.length
                                ? t("marzyar.deselectAll", "Deselect All")
                                : t("marzyar.selectAll", "Select All")}
                            </Button>
                          </HStack>
                          <Text fontSize="2xs" color="gray.500" mb={2}>
                            {allowedInbounds.length === 0
                              ? t("marzyar.allInboundsAllowed", "All inbounds are allowed by default.")
                              : t(
                                  "marzyar.inboundsRestricted",
                                  "Admin can only assign users to selected inbounds."
                                )}
                          </Text>
                          <SimpleGrid
                            columns={{ base: 1, sm: 2 }}
                            spacing={1.5}
                            maxH="130px"
                            overflowY="auto"
                            p={1}
                          >
                            {availableInbounds.map((tag) => {
                              const isChecked = allowedInbounds.includes(tag);
                              return (
                                <HStack
                                  key={tag}
                                  p={1.5}
                                  px={2.5}
                                  borderRadius="md"
                                  borderWidth="1px"
                                  borderColor={isChecked ? "primary.500" : "light-border"}
                                  bg={isChecked ? "primary.50" : "transparent"}
                                  _dark={{
                                    borderColor: isChecked ? "primary.400" : "gray.600",
                                    bg: isChecked ? "whiteAlpha.100" : "transparent",
                                  }}
                                  cursor="pointer"
                                  onClick={() => toggleInbound(tag)}
                                  transition="all 0.15s ease"
                                >
                                  <Checkbox
                                    size="sm"
                                    isChecked={isChecked}
                                    onChange={() => toggleInbound(tag)}
                                    colorScheme="primary"
                                    pointerEvents="none"
                                  />
                                  <Text fontSize="xs" fontWeight={isChecked ? "semibold" : "normal"}>
                                    {tag}
                                  </Text>
                                </HStack>
                              );
                            })}
                          </SimpleGrid>
                        </Box>
                      )}
                    </VStack>
                  </Box>
                </Collapse>

                <Divider borderColor="light-border" _dark={{ borderColor: "gray.700" }} my={1} />

                {/* Management Quick Actions */}
                <Box>
                  <Text fontSize="xs" fontWeight="semibold" color="gray.500" mb={2}>
                    {t("admins.quickActions", "Quick Actions")}
                  </Text>
                  <HStack spacing={2} wrap="wrap">
                    <Button
                      size="xs"
                      variant="outline"
                      colorScheme="orange"
                      onClick={handleResetUsage}
                      isLoading={actionLoading === "resetUsage"}
                      leftIcon={<ArrowPathIcon width="14px" />}
                    >
                      {t("admins.resetUsage")}
                    </Button>
                    <Button
                      size="xs"
                      variant="outline"
                      colorScheme="red"
                      onClick={handleDisableUsers}
                      isLoading={actionLoading === "disableUsers"}
                      leftIcon={<NoSymbolIcon width="14px" />}
                    >
                      {t("admins.disableUsers")}
                    </Button>
                    <Button
                      size="xs"
                      variant="outline"
                      colorScheme="green"
                      onClick={handleActivateUsers}
                      isLoading={actionLoading === "activateUsers"}
                      leftIcon={<CheckCircleIcon width="14px" />}
                    >
                      {t("admins.activateUsers")}
                    </Button>
                  </HStack>
                </Box>
              </VStack>
            </ModalBody>

            <ModalFooter justifyContent="space-between" pt={2} pb={5}>
              <Box>
                {!editingAdmin.is_sudo && (
                  <Tooltip label={t("deleteAdmin.title", "Delete Admin")} placement="top">
                    <Button
                      colorScheme="red"
                      variant="ghost"
                      size="sm"
                      leftIcon={<TrashIcon width="16px" />}
                      onClick={() => {
                        const adminToDelete = editingAdmin;
                        onClose();
                        setDeletingAdmin(adminToDelete);
                      }}
                    >
                      {t("delete")}
                    </Button>
                  </Tooltip>
                )}
              </Box>
              <HStack spacing={2}>
                <Button variant="ghost" onClick={onClose} size="sm">
                  {t("cancel")}
                </Button>
                <Button
                  type="submit"
                  colorScheme="primary"
                  size="sm"
                  px={6}
                  isLoading={isUpdating}
                >
                  {t("admins.editAdmin")}
                </Button>
              </HStack>
            </ModalFooter>
          </form>
        )}
      </ModalContent>
    </Modal>
  );
};
