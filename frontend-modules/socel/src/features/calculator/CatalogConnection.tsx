import { CheckCircle2Icon, ExternalLinkIcon } from "lucide-react";
import { type FormEvent, useState } from "react";
import { Button, Flex, Link, Text, TextField } from "../../components";
import { errorMessage } from "../../lib/errors";
import { type FactorCatalog, useCatalogKey } from "./useFactorCatalogs";

// Whether the catalog can be consulted, and the user's key for it: asked for
// when there is none, and changed or forgotten once there is. A key set for the
// installation (.env) is only named, not changed here.
export default function CatalogConnection({ catalog }: { catalog: FactorCatalog }) {
  const [isEditing, setEditing] = useState(false);
  const { disconnect, isDisconnecting, error } = useCatalogKey(catalog.id);

  if (catalog.key === "environment") {
    return <Connected>{catalog.name} is connected.</Connected>;
  }

  if (catalog.key === "saved" && !isEditing) {
    return (
      <Flex direction="column" gap="2">
        <Flex align="center" justify="between" gap="3" wrap="wrap">
          <Connected>{catalog.name} is connected with your key.</Connected>
          <Flex gap="2">
            <Button size="1" variant="soft" color="gray" onClick={() => setEditing(true)}>
              Change key
            </Button>
            <Button
              size="1"
              variant="soft"
              color="red"
              loading={isDisconnecting}
              onClick={() => void disconnect().catch(() => undefined)}
            >
              Disconnect
            </Button>
          </Flex>
        </Flex>
        {error !== null && (
          <Text size="2" color="red">
            {errorMessage(error)}
          </Text>
        )}
      </Flex>
    );
  }

  return (
    <KeyForm
      catalog={catalog}
      onConnected={() => setEditing(false)}
      onCancel={catalog.key === "saved" ? () => setEditing(false) : undefined}
    />
  );
}

function Connected({ children }: { children: string | string[] }) {
  return (
    <Flex align="center" gap="2">
      <CheckCircle2Icon size={16} color="var(--green-10)" aria-hidden />
      <Text size="2">{children}</Text>
    </Flex>
  );
}

// The key, with a link to the catalog's website to sign up for one. The
// catalog checks it before it is kept; a refused key says so here.
function KeyForm({
  catalog,
  onConnected,
  onCancel,
}: {
  catalog: FactorCatalog;
  onConnected: () => void;
  /** Leaves the key as it was; only when there is one. */
  onCancel?: () => void;
}) {
  const [key, setKey] = useState("");
  const { connect, isConnecting, error } = useCatalogKey(catalog.id);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    connect(key.trim())
      .then(onConnected)
      .catch(() => undefined);
  };

  return (
    <form onSubmit={submit}>
      <Flex direction="column" gap="2">
        <Flex align="center" justify="between" gap="3">
          <Text as="label" size="2" weight="medium" htmlFor={`catalog-key-${catalog.id}`}>
            {catalog.name} API key
          </Text>
          <Link size="2" href={catalog.website} target="_blank" rel="noreferrer">
            <Flex as="span" align="center" gap="1">
              Sign up
              <ExternalLinkIcon size={12} aria-hidden />
            </Flex>
          </Link>
        </Flex>
        <Flex gap="2" align="center">
          <TextField.Root
            id={`catalog-key-${catalog.id}`}
            type="password"
            autoComplete="off"
            placeholder="Paste the key"
            value={key}
            onChange={(event) => setKey(event.target.value)}
            style={{ flexGrow: 1 }}
          />
          {onCancel && (
            <Button type="button" variant="soft" color="gray" onClick={onCancel}>
              Cancel
            </Button>
          )}
          <Button type="submit" disabled={key.trim() === ""} loading={isConnecting}>
            Connect
          </Button>
        </Flex>
        {error !== null && (
          <Text size="2" color="red">
            {errorMessage(error)}
          </Text>
        )}
      </Flex>
    </form>
  );
}
