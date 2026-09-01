<template>
    <ToolTip :x="wX" :y="wY" :data="warning" align="right">
        <template v-slot:default>
            <div>
                <div>{{ warning.tag_name }} ({{ warning.count }})</div>
                <div>{{ warning.explanation }}</div>
                <div class="d-flex flex-wrap" style="max-width: 100%;">
                    <ItemTeaser 
                        v-for="id in warning.items"
                        :id="id"
                        :width="100"
                        :height="50"
                        :border-size="3"
                        :border-color="isVerySimilar(id) ? verySimCol : normalCol"
                        class="mr-1 mb-1"/>
                    <ItemTeaser 
                        v-for="id in warning.otherItems"
                        :id="id"
                        :width="100"
                        :height="50"
                        :border-size="3"
                        :border-color="isVerySimilar(id) ? verySimCol : normalCol"
                        style="opacity: 35%;"
                        class="mr-1 mb-1"/>
                </div>
            </div>
        </template>
    </ToolTip>
</template>

<script setup>
    import { useTooltip } from '@/store/tooltip';
    import ToolTip from '../ToolTip.vue';
    import { storeToRefs } from 'pinia';
    import ItemTeaser from '../items/ItemTeaser.vue';
    import { useTheme } from 'vuetify';
    import { computed } from 'vue';

    const tt = useTooltip()
    const { warning, wX, wY } = storeToRefs(tt)

    const theme = useTheme()

    const verySimCol = computed(() => theme.current.value.colors.primary)
    const normalCol = computed(() => theme.current.value.colors.background)

    function isVerySimilar(id) {
        if (!warning.value) return false
        return warning.value.verySimilar.has(id)
    }

</script>