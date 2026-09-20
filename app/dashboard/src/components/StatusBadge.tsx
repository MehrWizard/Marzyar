import { Badge, Text } from "@chakra-ui/react";

import { statusColors } from "constants/UserSettings";
import { FC } from "react";
import { useTranslation } from "react-i18next";
import { Status as UserStatusType } from "types/User";
import { relativeExpiryDate } from "utils/dateFormatter";

type UserStatusProps = {
  expiryDate?: number | null;
  status: UserStatusType;
  compact?: boolean;
  showDetail?: boolean;
  extraText?: string | null;
  isLocked?: boolean;
};
export const StatusBadge: FC<UserStatusProps> = ({
  expiryDate,
  status: userStatus,
  compact = false,
  showDetail = true,
  extraText,
  isLocked = false,
}) => {
  const { t } = useTranslation();
  const dateInfo = relativeExpiryDate(expiryDate);
  const activeConfig = isLocked ? statusColors["locked"] : (statusColors[userStatus] || statusColors["disabled"]);
  const Icon = activeConfig.icon;
  return (
    <>
      <Badge
        colorScheme={activeConfig.statusColor}
        rounded="full"
        display="inline-flex"
        px={3}
        py={1}
        columnGap={compact ? 1 : 2}
        alignItems="center"
        title={isLocked ? t("status.locked_tooltip", "Locked: Admin Quota Exceeded") : undefined}
      >
        <Icon w={compact ? 3 : 4} />
        {showDetail && (
          <Text
            textTransform="capitalize"
            fontSize={compact ? ".7rem" : ".875rem"}
            lineHeight={compact ? "1rem" : "1.25rem"}
            fontWeight="medium"
            letterSpacing="tighter"
          >
            {isLocked ? t("status.locked", "Locked") : (userStatus && t(`status.${userStatus}`))}
            {extraText && `: ${extraText}`}
          </Text>
        )}
      </Badge>
      {showDetail && expiryDate && (
        <Text
          display="inline-block"
          fontSize="xs"
          fontWeight="medium"
          ml="2"
          color="gray.600"
          _dark={{
            color: "gray.400",
          }}
        >
          {t(dateInfo.status, { time: dateInfo.time })}
        </Text>
      )}
    </>
  );
};
