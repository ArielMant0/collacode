<template>
    <div class="d-flex align-center">
        <v-select v-model="method"
            :items="DR_METHODS"
            @update:model-value="emit('update', getParams())"
            density="compact"
            class="mr-1"
            :variant="variant"
            hide-details
            hide-spin-buttons/>
        <div v-if="method === METHODS.TSNE" class="d-flex">
            <v-select v-model="metric"
                :items="METRICS"
                hide-details
                hide-spin-buttons
                single-line
                :variant="variant"
                @update:model-value="emit('update', getParams())"
                density="compact"/>
            <v-number-input v-model="perplexity"
                density="compact"
                label="perplexity"
                controlVariant="stacked"
                class="ml-1"
                :min="2"
                :variant="variant"
                single-line
                hide-details
                @update:model-value="emit('update', getParams())"
                hide-spin-buttons/>
            <!-- <v-number-input v-model="epsilon"
                density="compact"
                label="epsilon"
                controlVariant="stacked"
                class="ml-1"
                :min="2"
                :variant="variant"
                single-line
                hide-details
                @update:model-value="emit('update', getParams())"
                hide-spin-buttons/> -->
        </div>
        <div v-else-if="method === METHODS.UMAP" class="d-flex">
            <v-select v-model="metric"
                :items="METRICS"
                hide-details
                hide-spin-buttons
                :variant="variant"
                single-line
                @update:model-value="emit('update', getParams())"
                density="compact"/>
            <v-number-input v-model="neighbors"
                density="compact"
                label="neighbors"
                controlVariant="stacked"
                class="ml-1"
                :min="2"
                :variant="variant"
                single-line
                hide-details
                @update:model-value="emit('update', getParams())"
                hide-spin-buttons/>
            <v-number-input v-model="localConn"
                density="compact"
                label="local connectivity"
                controlVariant="stacked"
                class="ml-1"
                :min="2"
                :variant="variant"
                single-line
                hide-details
                @update:model-value="emit('update', getParams())"
                hide-spin-buttons/>
            <v-number-input v-model="epochs"
                density="compact"
                label="epochs"
                controlVariant="stacked"
                class="ml-1"
                :min="100"
                :variant="variant"
                single-line
                hide-details
                @update:model-value="emit('update', getParams())"
                hide-spin-buttons/>
        </div>
        <div v-else-if="method === METHODS.TOPOPMAP || method === METHODS.MDS" class="d-flex">
            <v-select v-model="metric"
                :items="METRICS"
                hide-details
                hide-spin-buttons
                :variant="variant"
                single-line
                @update:model-value="emit('update', getParams())"
                density="compact"/>
        </div>
    </div>
</template>

<script setup>
    import { ref } from 'vue';
    import { getMetric } from '@/use/metrics';

    const props = defineProps({
        variant: {
            type: String,
            default: "solo"
        },
        defaults: {
            type: Object,
            default: () => ({})
        }
    })

    const METRICS = ["cosine", "euclidean"]
    const METHODS = Object.freeze({
        PCA: "PCA",
        TSNE: "TSNE",
        UMAP: "UMAP",
        TOPOPMAP: "TopoMap",
        MDS: "MDS"
    })
    const DR_METHODS = Object.values(METHODS)
    const BASE_DEFAULTS = Object.freeze({
        method: 'TSNE',
        metric: 'cosine',
        perplexity: 25,
        // epsilon: 10,
        neighbors: 15,
        localConn: 3,
        epochs: 500
    })

    const emit = defineEmits(["update"])

    const defaults = Object.assign(Object.assign({}, BASE_DEFAULTS), props.defaults)
    const method = ref(defaults.method)
    const metric = ref(defaults.metric)

    const perplexity = ref(defaults.perplexity)
    // const epsilon = ref(defaults.epsilon)

    const neighbors = ref(defaults.neighbors)
    const localConn = ref(defaults.localConn)
    const epochs = ref(defaults.epochs)

    function getParams() {
        switch (method.value) {
            case METHODS.PCA: return { method: method.value }
            case METHODS.TSNE: return {
                method: method.value,
                metric: metric.value,
                perplexity: perplexity.value
            }
            case METHODS.UMAP: return {
                method: method.value,
                metric: metric.value,
                n_neighbors: neighbors.value,
                local_connectivity: localConn.value,
                _n_epochs: epochs.value
            }
            default: return {
                method: method.value,
                metric: metric.value
            }
        }
    }

    defineExpose({ getParams })
</script>