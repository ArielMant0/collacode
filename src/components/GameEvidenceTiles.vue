<template>
    <div>
        <div v-for="d in data.games" class="d-flex justify-start ma-1" style="width: 100%;">

            <div class="mr-2">
                <v-hover>
                    <template v-slot:default="{ isHovering, props }">
                        <v-img v-bind="props"
                            :src="'teaser/'+d.teaser"
                            :lazy-src="imgUrlS"
                            cover
                            :width="width"
                            :height="height">
                            <v-overlay :model-value="isHovering" contained class="d-flex align-center justify-center" opacity="0.75">
                                <span style="color: white; white-space: break-spaces; text-align: center;" class="pa-1 font-weight-bold">{{ d.name }}</span>
                            </v-overlay>
                        </v-img>
                    </template>
                </v-hover>
            </div>

            <v-sheet v-for="e in data.evidence.get(d.id)" class="pa-0 mr-2" :width="showDesc.has(e.id) ? 500 : height">

                <v-hover v-if="e.filepath">
                    <template v-slot:default="{ isHovering, props }">
                        <v-img v-bind="props"
                            class="cursor-pointer"
                            :src="'evidence/'+e.filepath"
                            cover
                            @click="enlarge(e)"
                            v-ripple.center
                            :width="showDesc.has(e.id) ? 500 : height-10"
                            :height="showDesc.has(e.id) ? 300 : height-10">
                            <v-overlay :model-value="isHovering" contained class="d-flex align-center justify-center" opacity="0.75">
                                <v-icon size="64" color="grey-lighten-2">mdi-magnify-plus-outline</v-icon>
                            </v-overlay>
                        </v-img>
                    </template>
                </v-hover>
                <div v-else>
                    <v-img class="pa-1" :src="imgUrlS" :width="height-10" :height="height-10"/>
                </div>

                <div class="d-flex cursor-pointer" @click="toggleDesc(e.id)">
                    <v-icon :icon="showDesc.has(e.id) ? 'mdi-menu-down' : 'mdi-menu-right'" density="compact"/>
                    <v-tooltip v-if="e.tag" :text="e.tag.name" open-delay="200" location="right">
                        <template v-slot:activator="{ props }">
                            <div v-bind="props" class="text-caption text-dots" style="max-width: 100%;">{{ e.tag.name }}</div>
                        </template>
                    </v-tooltip>
                </div>

                <v-card v-if="showDesc.has(e.id)" :text="e.description" width="500"></v-card>
            </v-sheet>
        </div>

        <v-overlay v-model="showEnlarged" opacity="0.8"
            class="d-flex align-center justify-center"
            @update:model-value="checkEnlarge"
            close-on-content-click>
            <div v-if="enlargedItem" class="pa-3">
                <img :src="'evidence/'+enlargedItem.filepath" style="max-width: 100%;" alt="Image Preview"/>
                <v-card class="mt-2" color="grey-darken-4" :text="enlargedItem.description"></v-card>
            </div>
        </v-overlay>
    </div>
</template>

<script setup>
    import * as d3 from 'd3';
    import { reactive, onMounted, watch, ref } from 'vue';
    import DM from '@/use/data-manager'

    import imgUrlS from '@/assets/__placeholder__s.png'

    const props = defineProps({
        time: {
            type: Number,
            required: true
        },
        code: {
            type: Number
        },
        selected: {
            type: Object,
            required: false
        },
        highlightClicked: {
            type: Boolean,
            default: false
        },
        width: {
            type: Number,
            default: 150
        },
        height: {
            type: Number,
            default: 75
        },
    });

    const enlargedItem = ref(null);
    const showEnlarged = ref(false);

    const data = reactive({
        games: [],
        tags: [],
        evidence: new Map()
    })
    const showDesc = reactive(new Set());

    function readData() {
        const gameIds = new Set();
        data.games = DM.getData("games", true);
        data.games.forEach(d => gameIds.add(d.id));
        readEvidence();
    }
    function readEvidence() {
        const gameIds = new Set(DM.getSelectedIds("games"));
        const tagIds = new Set(DM.getSelectedIds("tags"));
        showDesc.clear();
        if (props.code && gameIds.size > 0) {
            const ev = DM.getDataBy("evidence", d => {
                return d.code_id === props.code &&
                    gameIds.has(d.game_id) &&
                    (tagIds.size === 0 || d.tag_id && tagIds.has(d.tag_id))
        });
            data.evidence = d3.group(ev, d => d.game_id)
        } else {
            data.evidence.clear();
        }
        readTags();
    }
    function readTags() {
        const tags = DM.getData("tags", false);
        data.evidence.forEach(array => array.forEach(d => {
            d.tag = d.tag_id ? tags.find(t => t.id === d.tag_id) : null
        }));
    }

    function toggleDesc(id) {
        if (showDesc.has(id)) {
            showDesc.delete(id)
        } else {
            showDesc.add(id)
        }
    }
    function enlarge(item) {
        if (item) {
            enlargedItem.value = item;
            showEnlarged.value = true;
        }
    }
    function checkEnlarge() {
        if (!showEnlarged.value) {
            enlargedItem.value = null;
        }
    }
    onMounted(readData)

    watch(() => props.time, readData)
</script>

<style scoped>
.text-dots {
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis
}</style>