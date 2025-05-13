import { getMetric } from '@/use/metrics';
import * as druid from '@saehrimnir/druidjs';

onmessage = (e) => {
    const dr = getDR(e.data.params, e.data.matrix)
    postMessage(Array.from(dr.transform()));
};

function getDR(params, data) {
    params.metric = getMetric(params.metric)
    const method = params.method;
    delete params.method

    if (!data || data.length === 0) {
        console.warn("empty matrix")
        return;
    }

    const matrix = druid.Matrix.from(data)

    const DR = druid[method]
    switch (method) {
        // case "ISOMAP": return new DR(matrix, { metric: druid.cosine })
        case "TopoMap": return new DR(matrix, params)
        case "MDS": return new DR(matrix, params)
        case "TSNE": return new DR(matrix, params)
        case "UMAP": return new DR(matrix, params)
        default: return new DR(matrix)
    }
}
