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
  Select,
  SimpleGrid,
  Switch,
  Text,
  useToast,
  VStack,
} from "@chakra-ui/react";
import {
  AdjustmentsHorizontalIcon,
  EyeIcon,
  EyeSlashIcon,
  ShieldCheckIcon,
  UserPlusIcon,
} from "@heroicons/react/24/outline";
import { zodResolver } from "@hookform/resolvers/zod";
import { FetchAdminsQueryKey, useAdmins } from "contexts/AdminsContext";
import { useDashboard } from "contexts/DashboardContext";
import { FetchMarzyarAdminsQueryKey, useMarzyar } from "contexts/MarzyarContext";
import { FC, useMemo, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { useMutation, useQueryClient } from "react-query";
import { AdminCreate, AdminCreateSchema } from "types/Admin";
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

const ModalIcon = chakra(UserPlusIcon, {
  baseStyle: {
    w: 5,
    h: 5,
  },
});

export const CreateAdminModal: FC = () => {
  const { isCreatingAdmin, setIsCreatingAdmin, createAdmin } = useAdmins();
  const { inbounds } = useDashboard();
  const { t } = useTranslation();
  const toast = useToast();
  const queryClient = useQueryClient();
  const [showPassword, setShowPassword] = useState(false);

  // Marzyar Reseller state
  const [usersLimit, setUsersLimit] = useState<string>("");
  const [trafficLimit, setTrafficLimit] = useState<string>("");
  const [trafficLimitUnit, setTrafficLimitUnit] = useState<"GB" | "TB">("GB");
  const [oversellAllowed, setOversellAllowed] = useState<boolean>(false);
  const [allowedInbounds, setAllowedInbounds] = useState<string[]>([]);

  const form = useForm<AdminCreate>({
    resolver: zodResolver(AdminCreateSchema),
    defaultValues: {
      username: "",
      password: "",
      is_sudo: false,
      telegram_id: null,
      discord_webhook: "",
    },
  });

  const isSudoValue = form.watch("is_sudo");

  // Extract all unique inbound tags
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

  const onClose = () => {
    form.reset();
    setUsersLimit("");
    setTrafficLimit("");
    setTrafficLimitUnit("GB");
    setOversellAllowed(false);
    setAllowedInbounds([]);
    setIsCreatingAdmin(false);
  };

  const { isLoading, mutate: onCreate } = useMutation(
    async (data: AdminCreate) => {
      const created = await createAdmin(data);

      // If created as a regular admin, apply Marzyar settings if configured
      if (!data.is_sudo) {
        const uLimit = usersLimit.trim() ? parseInt(usersLimit) : null;
        let tLimit: number | null = null;
        if (trafficLimit.trim() && Number(trafficLimit) > 0) {
          const mult = trafficLimitUnit === "TB" ? 1099511627776 : 1073741824;
          tLimit = Math.round(Number(trafficLimit) * mult);
        }
        const inboundsPayload = allowedInbounds.length > 0 ? allowedInbounds : null;

        await useMarzyar.getState().updateAdminSettings(data.username, {
          users_limit: uLimit,
          traffic_limit: tLimit,
          oversell_allowed: oversellAllowed,
          allowed_inbounds: inboundsPayload,
        });
      }

      return created;
    },
    {
      onSuccess: () => {
        generateSuccessMessage(
          t("admins.addAdminSuccess", { username: form.getValues("username") }),
          toast
        );
        queryClient.invalidateQueries(FetchAdminsQueryKey);
        queryClient.invalidateQueries(FetchMarzyarAdminsQueryKey);
        onClose();
      },
      onError: (e) => {
        generateErrorMessage(e, toast, form);
      },
    }
  );

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

  return (
    <Modal isOpen={isCreatingAdmin} onClose={onClose} isCentered size="lg">
      <ModalOverlay bg="blackAlpha.400" backdropFilter="blur(8px)" />
      <ModalContent mx={3} maxH="90vh" overflowY="auto">
        <ModalHeader display="flex" alignItems="center" gap={3} pt={5}>
          <Icon color="primary">
            <ModalIcon color="white" />
          </Icon>
          <Box>
            <Text fontSize="lg" fontWeight="semibold">
              {t("admins.addNewAdmin")}
            </Text>
            <Text fontSize="xs" color="gray.500" fontWeight="normal">
              {t("admins.createAdminSubtitle", "Create a new administrator or reseller account")}
            </Text>
          </Box>
        </ModalHeader>
        <ModalCloseButton mt={3} />

        <form onSubmit={form.handleSubmit((data) => onCreate(data))}>
          <ModalBody py={4}>
            <VStack spacing={4} align="stretch">
              <CustomInput
                label={t("admins.username")}
                placeholder="admin_username"
                {...form.register("username")}
                error={form.formState?.errors?.username?.message}
                autoFocus
              />

              <FormControl isInvalid={!!form.formState?.errors?.password}>
                <FormLabel fontSize="xs" mb={1} color="gray.600" _dark={{ color: "gray.400" }}>
                  {t("admins.password")}
                </FormLabel>
                <InputGroup size="md">
                  <ChakraInput
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
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
                {form.formState?.errors?.password && (
                  <Text color="red.500" fontSize="xs" mt={1}>
                    {form.formState.errors.password.message}
                  </Text>
                )}
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
                  <HStack spacing={2} mb={3}>
                    <AdjustmentsHorizontalIcon width="18px" height="18px" />
                    <Text fontSize="sm" fontWeight="bold">
                      {t("marzyar.resellerLimits", "Reseller Limits & Quota")}
                    </Text>
                    <Badge colorScheme="blue" fontSize="2xs">
                      Marzyar
                    </Badge>
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
                        <SimpleGrid columns={{ base: 1, sm: 2 }} spacing={1.5} maxH="130px" overflowY="auto" p={1}>
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
            </VStack>
          </ModalBody>

          <ModalFooter gap={2} pt={2} pb={5}>
            <Button variant="ghost" onClick={onClose} size="sm">
              {t("cancel")}
            </Button>
            <Button
              type="submit"
              colorScheme="primary"
              size="sm"
              px={6}
              isLoading={isLoading}
            >
              {t("admins.addAdmin")}
            </Button>
          </ModalFooter>
        </form>
      </ModalContent>
    </Modal>
  );
};
