import * as d3 from 'd3'

onmessage = function(event) {
    const weightAttr = event.data.weightAttr,
        maxWeight = event.data.maxWeight,
        radius = event.data.radius,
        width = event.data.width,
        height = event.data.height

    const nodes = event.data.nodes,
        links = event.data.links;

    function distanceFunction(d) {
        return (1 + ((maxWeight - d[weightAttr]) / maxWeight)) * radius
    }

    const simulation = d3.forceSimulation(nodes)
            .alphaDecay(nodes.length < 100 ? 0.025 : 0.001)
            .force('link', d3.forceLink(links).id(d => d.id).distance(distanceFunction))
            .force('charge', d3.forceManyBody().strength(-10))
            .force('collide', d3.forceCollide(radius / 2))
            .force('center', d3.forceCenter(width / 2, height / 2).strength(0.5))
            .stop()

    for (let i = 0, n = Math.ceil(Math.log(simulation.alphaMin()) / Math.log(1 - simulation.alphaDecay())); i < n; ++i) {
        postMessage({ type: "tick", progress: Math.round((i+1) / n * 100) });
        simulation.tick();
    }

    postMessage({type: "end", nodes: nodes, links: links});

    // terminate itself
    self.close();
};
