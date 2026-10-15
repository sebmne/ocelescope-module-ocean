import { SunburstChart } from "@ocelescope/core";
import { BoxIcon, CogIcon, TagsIcon } from "lucide-react";
import {
  AsyncBoundary,
  type BarNode,
  BarTree,
  Box,
  Grid,
  Section,
  SubHeading,
} from "../../components";
import { formatCount } from "../../lib/format";
import { type TaxonomyNode, taxonomyTree } from "./taxonomyTree";
import { type ClassCount, useClassCounts } from "./useClassCounts";

const toBar = (node: TaxonomyNode): BarNode => ({
  id: node.path ?? "unclassified",
  label: node.label,
  value: node.total,
  valueHint:
    node.own > 0 && node.children.length > 0
      ? `${formatCount(node.own)} directly, ${formatCount(node.total - node.own)} below`
      : undefined,
  tone: node.path === null ? "muted" : "neutral",
  children: node.children.map(toBar),
});

const toBars = (counts: readonly ClassCount[]) => taxonomyTree(counts).map(toBar);

// One ring per level of the class path. A class that ends before the deepest
// level fills the rings beyond it with an unlabelled piece, drawn invisible.
// Shades of the one accent: the classes are told apart by their place in the
// rings and their labels, not by hue.
const SHADES = ["#0D74CE", "#3E8FE0", "#5EB1EF", "#2160A9", "#8EC8F6", "#4C8BD9"];
const colorOf = (_scope: string, name: string) => {
  if (name === "") return "rgba(0, 0, 0, 0)";
  if (name === "unclassified") return "#B9BBC6";
  let hash = 0;
  for (const character of name) hash = (hash * 31 + character.charCodeAt(0)) >>> 0;
  return SHADES[hash % SHADES.length];
};

const toRings = (counts: readonly ClassCount[]) => {
  const depth = Math.max(1, ...counts.map((c) => (c.socelClass ?? "").split(".").length));
  const levels = Array.from({ length: depth }, (_, index) => `level${index}`);
  const rows = counts.map(({ socelClass, count }) => {
    const segments = socelClass === null ? ["unclassified"] : socelClass.split(".");
    return Object.fromEntries([
      ...levels.map((level, index) => [level, segments[index] ?? ""]),
      ["count", count],
    ]);
  });
  return { rows, levels };
};

// Objects and events per socel_class, as the taxonomy tree the classes span:
// a sunburst for the distribution, and bars for the numbers.
export default function ClassesSection() {
  const counts = useClassCounts();

  return (
    <Section icon={TagsIcon} title="Classes">
      <AsyncBoundary
        status={counts}
        loadingLabel="Reading the classes…"
        errorTitle="The classes could not be read"
        onRetry={() => void counts.refetch()}
      >
        {(data) => (
          <Grid columns={{ initial: "1", md: "2" }} gap="6">
            <Column icon={BoxIcon} title="Objects" counts={data.objects} />
            <Column icon={CogIcon} title="Events" counts={data.events} />
          </Grid>
        )}
      </AsyncBoundary>
    </Section>
  );
}

function Column({
  icon,
  title,
  counts,
}: {
  icon: typeof BoxIcon;
  title: string;
  counts: readonly ClassCount[];
}) {
  const { rows, levels } = toRings(counts);
  return (
    <Box>
      <SubHeading icon={icon} title={title} />
      <Box style={{ height: 300 }} mb="4">
        <SunburstChart
          rows={rows}
          x={levels[0]}
          y="count"
          path={levels}
          colorScope="socelClass"
          colorOf={colorOf}
        />
      </Box>
      <BarTree nodes={toBars(counts)} format={formatCount} openDepth={2} />
    </Box>
  );
}
