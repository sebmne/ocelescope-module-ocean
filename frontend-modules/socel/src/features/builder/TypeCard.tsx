import type { LucideIcon } from "lucide-react";
import { Box, Flex, Progress, Section, Text, useColorOf } from "../../components";
import { formatCount } from "../../lib/format";
import ClassSelect from "./ClassSelect";
import { type ClassOption, classifiedShare } from "./classOptions";
import type { TypeClassification } from "./useLogClassification";

interface TypeCardProps {
  icon: LucideIcon;
  title: string;
  /** The scope the names are coloured under, as everywhere in Ocelescope. */
  colorScope: "activity" | "objectType";
  types: readonly TypeClassification[];
  options: readonly ClassOption[];
  classOf: (name: string) => string | null;
  onChange: (name: string, socelClass: string | null) => void;
}

// The activities or the object types of the log, each with its class. The bar
// in the header fills with the share of events or objects that have one.
export default function TypeCard({
  icon,
  title,
  colorScope,
  types,
  options,
  classOf,
  onChange,
}: TypeCardProps) {
  const colorOf = useColorOf(colorScope);
  const max = Math.max(1, ...types.map((type) => type.count));
  const share = classifiedShare(types, classOf);

  return (
    <Section
      icon={icon}
      title={title}
      aside={
        <Flex align="center" gap="2" flexGrow="1" justify="end">
          <Progress value={share * 100} size="2" style={{ width: 120 }} />
          <Text size="2" color="gray" style={{ fontVariantNumeric: "tabular-nums", minWidth: 36 }}>
            {Math.round(share * 100)}%
          </Text>
        </Flex>
      }
    >
      <Flex direction="column" gap="1">
        {types.map((type) => (
          <Flex key={type.name} align="center" gap="3">
            <Box position="relative" flexGrow="1" minWidth="0">
              <Box
                position="absolute"
                inset="0"
                style={{
                  width: `${(type.count / max) * 100}%`,
                  background: "var(--gray-a3)",
                  borderRadius: "var(--radius-2)",
                }}
              />
              <Flex position="relative" align="center" justify="between" gap="3" px="2" py="2">
                <Flex align="center" gap="2" minWidth="0">
                  <span
                    aria-hidden
                    style={{
                      flex: "none",
                      width: 8,
                      height: 8,
                      borderRadius: "50%",
                      background: colorOf(type.name),
                    }}
                  />
                  <Text size="2" weight="medium" truncate>
                    {type.name}
                  </Text>
                </Flex>
                <Text size="2" color="gray" style={{ fontVariantNumeric: "tabular-nums" }}>
                  {formatCount(type.count)}
                </Text>
              </Flex>
            </Box>
            <ClassSelect
              label={`Class of ${type.name}`}
              options={options}
              value={classOf(type.name)}
              onChange={(socelClass) => onChange(type.name, socelClass)}
            />
          </Flex>
        ))}
      </Flex>
    </Section>
  );
}
