import React from 'react';

const TREND_GRAPHS = [
    {
        title: 'Temperature Trend',
        file: 'temperature_trend.html',
        description: 'Historical temperature variation over time.'
    },
    {
        title: 'Rainfall Trend',
        file: 'rainfall_trend.html',
        description: 'Historical rainfall pattern and variation.'
    },
    {
        title: 'Wind Trend',
        file: 'wind_trend.html',
        description: 'Historical wind speed and directional trend.'
    },
    {
        title: 'Wind Frequency Distribution',
        file: 'wind_frequency_distribution.html',
        description: 'Distribution of historical wind conditions.'
    },
    {
        title: 'Pressure Anomaly',
        file: 'pressure_anomaly.html',
        description: 'Historical atmospheric pressure anomalies.'
    },
    {
        title: 'Pressure Distribution',
        file: 'pressure_distribution.html',
        description: 'Distribution of historical pressure values.'
    },
    {
        title: 'Wind Rose - Direction 98m + Speed 100m',
        file: 'wind_rose.jpeg',
        description: 'Historical wind direction and speed distribution at 98m/100m.',
        type: 'image'
    }
];

export default function Historical({ node }) {

    return (
        <main className="page historical-page">

            <div className="page-head">
                <div>
                    <div className="eyebrow">
                        HISTORICAL / TREND
                    </div>

                    <h1>
                        {node.name} · Historical Analysis
                    </h1>

                    <p>
                        Historical environmental observations
                        and long-term trends for the selected
                        monitoring node.
                    </p>
                </div>

                <div className="chip">
                    HISTORICAL DATA
                </div>
            </div>


            <div className="trend-grid">

                {TREND_GRAPHS.map((graph) => (

                    <article
                        className="trend-card"
                        key={graph.file}
                    >

                        <div className="trend-card-header">

                            <div>
                                <h2>
                                    {graph.title}
                                </h2>

                                <p>
                                    {graph.description}
                                </p>
                            </div>

                        </div>


                        {graph.type === 'image' ? (
                            <img
                                src={`/Trends/${graph.file}`}
                                alt={graph.title}
                                className="trend-image"
                                loading="lazy"
                            />
                        ) : (
                            <iframe
                                src={`/Trends/${graph.file}`}
                                title={graph.title}
                                className="trend-iframe"
                                loading="lazy"
                            />
                        )}

                    </article>

                ))}

            </div>

        </main>
    );
}