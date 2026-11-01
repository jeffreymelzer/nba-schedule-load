"""
Plotting functions for displaying travel results and map data.
"""

import matplotlib.pyplot as plt


def plot_bar(summaries, key, title, path=None):
    """Horizontal bar chart of one summary metric per team, sorted high to low."""
    teams = sorted(summaries, key=lambda t: summaries[t][key])
    fig, ax = plt.subplots(figsize=(8, 9))
    ax.barh(teams, [summaries[t][key] for t in teams], color='#3b6ea5')
    ax.set_title(title)
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=150)

    return fig


def plot_route(team, team_schedule, city_lookup, path=None):
    """Draw a team's season as a line through its game cities, in game order, on the North America basemap."""
    import cartopy.crs as ccrs
    from modules.travel import city_key

    fig = plt.figure(figsize=(12, 8))
    ax = plot_basemap(fig)
    points = [city_lookup[city_key(city, state)] for _, city, state in team_schedule]
    # the two games abroad would stretch the map, so only the North American legs are drawn
    points = [p for p in points if -125 <= p[1] <= -65]
    ax.plot([p[1] for p in points], [p[0] for p in points], '-', color='#3b6ea5', linewidth=0.6, alpha=0.5,
            transform=ccrs.Geodetic())
    for lat, long in set(points):
        ax.plot(long, lat, 'o', color='#c0392b', markersize=4, transform=ccrs.PlateCarree())
    ax.set_title(f'{team} season route')
    if path:
        fig.savefig(path, dpi=150)

    return fig


def plot_basemap(fig):
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    crs = ccrs.LambertConformal(central_longitude=-100, central_latitude=45)

    ax = fig.add_subplot(1, 1, 1, projection=crs)
    ax.set_extent((-122, -75, 15, 50), crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidth=0.75)
    ax.add_feature(cfeature.STATES, linewidth=0.5)
    ax.axis('off')

    return ax
