# Embedding the dashboard in the portfolio site

The AI/BI dashboard is **published with embedded credentials** — it runs queries as the
publisher, so an embedded viewer needs no Databricks data grants. To show it on an external
site (e.g. `connect-insight-space`) **without a login prompt**, the viewer's domain must be
whitelisted once.

## One-time: whitelist your portfolio domain
Workspace **Settings → Security → AI/BI Dashboard embedding** → set
*"Allow embedding for an approved list of domains"* and add your site's domain
(e.g. `connect-insight-space.vercel.app`, `connectinsightspace.com`). Account-admin rights
required; this is a UI toggle, not a CLI call.

> Without this, the iframe still works but viewers are asked to sign in to the workspace.

## URLs
| Purpose            | URL |
|--------------------|-----|
| Published dashboard| `https://dbc-036c0f5b-a5d8.cloud.databricks.com/dashboardsv3/01f167fb84e01d88acaf62a3e633ad3e/published` |
| Embed (iframe src) | `https://dbc-036c0f5b-a5d8.cloud.databricks.com/embed/dashboardsv3/01f167fb84e01d88acaf62a3e633ad3e` |
| What-if app        | `https://energy-transition-whatif-4258774216266378.aws.databricksapps.com` |

> The dashboard id changes if the bundle is destroyed and redeployed. After a redeploy,
> grab the new id with `databricks lakeview list` and update the iframe.

## Plain HTML
```html
<iframe
  src="https://dbc-036c0f5b-a5d8.cloud.databricks.com/embed/dashboardsv3/01f167fb84e01d88acaf62a3e633ad3e"
  width="100%" height="800" frameborder="0" style="border:0;border-radius:12px"
  title="US Energy Transition dashboard"></iframe>
```

## React / Next.js component (for connect-insight-space)
```tsx
export function EnergyTransitionDashboard() {
  const src =
    "https://dbc-036c0f5b-a5d8.cloud.databricks.com/embed/dashboardsv3/01f167fb84e01d88acaf62a3e633ad3e";
  return (
    <div className="aspect-[3/4] w-full overflow-hidden rounded-xl border md:aspect-video">
      <iframe
        src={src}
        title="US Energy Transition dashboard"
        className="h-full w-full"
        loading="lazy"
      />
    </div>
  );
}
```

The what-if app can be linked or embedded the same way (its domain is the
`databricksapps.com` URL above; apps require viewer auth unless made public).
