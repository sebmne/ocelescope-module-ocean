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
  tone: node.path === null ? "muted" : node.isCore ? "accent" : "neutral",
  children: node.children.map(toBar),
});

const toBars = (counts: readonly ClassCount[]) => taxonomyTree(counts).map(toBar);

// Objects and events per socel_class, as the taxonomy tree the classes span;
// handling units and operations stand out.
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
            <Column icon={BoxIcon} title="Objects" nodes={toBars(data.objects)} />
            <Column icon={CogIcon} title="Events" nodes={toBars(data.events)} />
          </Grid>
        )}
      </AsyncBoundary>
    </Section>
  );
}

function Column({ icon, title, nodes }: { icon: typeof BoxIcon; title: string; nodes: BarNode[] }) {
  return (
    <Box>
      <SubHeading icon={icon} title={title} />
      <BarTree nodes={nodes} format={formatCount} openDepth={2} />
    </Box>
  );
}
