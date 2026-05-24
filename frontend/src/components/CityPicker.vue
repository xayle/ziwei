<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'

interface City {
  name: string
  province: string
  lng: number
}

const CITIES: City[] = [
  // 直辖市
  { name: '北京',    province: '北京市',   lng: 116.41 },
  { name: '天津',    province: '天津市',   lng: 117.19 },
  { name: '上海',    province: '上海市',   lng: 121.47 },
  { name: '重庆',    province: '重庆市',   lng: 106.55 },
  // 安徽省
  { name: '合肥',    province: '安徽省',   lng: 117.27 },
  { name: '芜湖',    province: '安徽省',   lng: 118.38 },
  { name: '蚌埠',    province: '安徽省',   lng: 117.37 },
  { name: '淮南',    province: '安徽省',   lng: 117.00 },
  { name: '马鞍山',  province: '安徽省',   lng: 118.51 },
  { name: '淮北',    province: '安徽省',   lng: 116.80 },
  { name: '铜陵',    province: '安徽省',   lng: 117.82 },
  { name: '安庆',    province: '安徽省',   lng: 117.05 },
  { name: '黄山',    province: '安徽省',   lng: 118.34 },
  { name: '滁州',    province: '安徽省',   lng: 118.32 },
  { name: '阜阳',    province: '安徽省',   lng: 115.82 },
  { name: '宿州',    province: '安徽省',   lng: 116.98 },
  { name: '六安',    province: '安徽省',   lng: 116.52 },
  { name: '亳州',    province: '安徽省',   lng: 115.78 },
  { name: '池州',    province: '安徽省',   lng: 117.49 },
  { name: '宣城',    province: '安徽省',   lng: 118.75 },
  // 福建省
  { name: '福州',    province: '福建省',   lng: 119.30 },
  { name: '厦门',    province: '福建省',   lng: 118.09 },
  { name: '莆田',    province: '福建省',   lng: 119.01 },
  { name: '三明',    province: '福建省',   lng: 117.64 },
  { name: '泉州',    province: '福建省',   lng: 118.67 },
  { name: '漳州',    province: '福建省',   lng: 117.65 },
  { name: '南平',    province: '福建省',   lng: 118.18 },
  { name: '龙岩',    province: '福建省',   lng: 117.02 },
  { name: '宁德',    province: '福建省',   lng: 119.53 },
  // 甘肃省
  { name: '兰州',    province: '甘肃省',   lng: 103.83 },
  { name: '嘉峪关',  province: '甘肃省',   lng:  98.29 },
  { name: '金昌',    province: '甘肃省',   lng: 102.19 },
  { name: '白银',    province: '甘肃省',   lng: 104.14 },
  { name: '天水',    province: '甘肃省',   lng: 105.73 },
  { name: '武威',    province: '甘肃省',   lng: 102.64 },
  { name: '张掖',    province: '甘肃省',   lng: 100.45 },
  { name: '平凉',    province: '甘肃省',   lng: 106.67 },
  { name: '酒泉',    province: '甘肃省',   lng:  98.49 },
  { name: '庆阳',    province: '甘肃省',   lng: 107.64 },
  { name: '定西',    province: '甘肃省',   lng: 104.62 },
  { name: '陇南',    province: '甘肃省',   lng: 104.92 },
  { name: '临夏',    province: '甘肃省',   lng: 103.21 },
  { name: '甘南',    province: '甘肃省',   lng: 102.91 },
  // 广东省
  { name: '广州',    province: '广东省',   lng: 113.26 },
  { name: '深圳',    province: '广东省',   lng: 114.06 },
  { name: '珠海',    province: '广东省',   lng: 113.58 },
  { name: '汕头',    province: '广东省',   lng: 116.69 },
  { name: '佛山',    province: '广东省',   lng: 113.13 },
  { name: '韶关',    province: '广东省',   lng: 113.60 },
  { name: '河源',    province: '广东省',   lng: 114.70 },
  { name: '梅州',    province: '广东省',   lng: 116.12 },
  { name: '惠州',    province: '广东省',   lng: 114.41 },
  { name: '汕尾',    province: '广东省',   lng: 115.37 },
  { name: '东莞',    province: '广东省',   lng: 113.75 },
  { name: '中山',    province: '广东省',   lng: 113.38 },
  { name: '江门',    province: '广东省',   lng: 113.08 },
  { name: '阳江',    province: '广东省',   lng: 111.98 },
  { name: '湛江',    province: '广东省',   lng: 110.36 },
  { name: '茂名',    province: '广东省',   lng: 110.93 },
  { name: '肇庆',    province: '广东省',   lng: 112.47 },
  { name: '清远',    province: '广东省',   lng: 113.06 },
  { name: '潮州',    province: '广东省',   lng: 116.63 },
  { name: '揭州',    province: '广东省',   lng: 116.37 },
  { name: '云浮',    province: '广东省',   lng: 112.04 },
  // 广西壮族自治区
  { name: '南宁',    province: '广西壮族自治区', lng: 108.37 },
  { name: '柳州',    province: '广西壮族自治区', lng: 109.41 },
  { name: '桂林',    province: '广西壮族自治区', lng: 110.30 },
  { name: '梧州',    province: '广西壮族自治区', lng: 111.28 },
  { name: '北海',    province: '广西壮族自治区', lng: 109.12 },
  { name: '防城港',  province: '广西壮族自治区', lng: 108.36 },
  { name: '钦州',    province: '广西壮族自治区', lng: 108.63 },
  { name: '贵港',    province: '广西壮族自治区', lng: 109.60 },
  { name: '玉林',    province: '广西壮族自治区', lng: 110.18 },
  { name: '百色',    province: '广西壮族自治区', lng: 106.62 },
  { name: '贺州',    province: '广西壮族自治区', lng: 111.57 },
  { name: '河池',    province: '广西壮族自治区', lng: 108.08 },
  { name: '来宾',    province: '广西壮族自治区', lng: 109.23 },
  { name: '崇左',    province: '广西壮族自治区', lng: 107.35 },
  // 贵州省
  { name: '贵阳',    province: '贵州省',   lng: 106.63 },
  { name: '六盘水',  province: '贵州省',   lng: 104.83 },
  { name: '遵义',    province: '贵州省',   lng: 106.93 },
  { name: '安顺',    province: '贵州省',   lng: 105.97 },
  { name: '毕节',    province: '贵州省',   lng: 105.29 },
  { name: '铜仁',    province: '贵州省',   lng: 109.19 },
  { name: '黔西南',  province: '贵州省',   lng: 104.90 },
  { name: '黔东南',  province: '贵州省',   lng: 107.98 },
  { name: '黔南',    province: '贵州省',   lng: 107.52 },
  // 海南省
  { name: '海口',    province: '海南省',   lng: 110.35 },
  { name: '三亚',    province: '海南省',   lng: 109.51 },
  { name: '三沙',    province: '海南省',   lng: 112.34 },
  { name: '儋州',    province: '海南省',   lng: 109.58 },
  // 河北省
  { name: '石家庄',  province: '河北省',   lng: 114.50 },
  { name: '唐山',    province: '河北省',   lng: 118.18 },
  { name: '秦皇岛',  province: '河北省',   lng: 119.60 },
  { name: '邯郸',    province: '河北省',   lng: 114.53 },
  { name: '邢台',    province: '河北省',   lng: 114.50 },
  { name: '保定',    province: '河北省',   lng: 115.47 },
  { name: '张家口',  province: '河北省',   lng: 114.88 },
  { name: '承德',    province: '河北省',   lng: 117.96 },
  { name: '沧州',    province: '河北省',   lng: 116.84 },
  { name: '廊坊',    province: '河北省',   lng: 116.68 },
  { name: '衡水',    province: '河北省',   lng: 115.67 },
  // 河南省
  { name: '郑州',    province: '河南省',   lng: 113.65 },
  { name: '开封',    province: '河南省',   lng: 114.31 },
  { name: '洛阳',    province: '河南省',   lng: 112.45 },
  { name: '平顶山',  province: '河南省',   lng: 113.19 },
  { name: '安阳',    province: '河南省',   lng: 114.40 },
  { name: '鹤壁',    province: '河南省',   lng: 114.30 },
  { name: '新乡',    province: '河南省',   lng: 113.92 },
  { name: '焦作',    province: '河南省',   lng: 113.24 },
  { name: '濮阳',    province: '河南省',   lng: 115.03 },
  { name: '许昌',    province: '河南省',   lng: 113.85 },
  { name: '漯河',    province: '河南省',   lng: 114.02 },
  { name: '三门峡',  province: '河南省',   lng: 111.19 },
  { name: '南阳',    province: '河南省',   lng: 112.53 },
  { name: '商丘',    province: '河南省',   lng: 115.65 },
  { name: '信阳',    province: '河南省',   lng: 114.09 },
  { name: '周口',    province: '河南省',   lng: 114.70 },
  { name: '驻马店',  province: '河南省',   lng: 114.02 },
  // 黑龙江省
  { name: '哈尔滨',  province: '黑龙江省', lng: 126.69 },
  { name: '齐齐哈尔',province: '黑龙江省', lng: 123.92 },
  { name: '鸡西',    province: '黑龙江省', lng: 130.97 },
  { name: '鹤岗',    province: '黑龙江省', lng: 130.30 },
  { name: '双鸭山',  province: '黑龙江省', lng: 131.16 },
  { name: '大庆',    province: '黑龙江省', lng: 125.10 },
  { name: '伊春',    province: '黑龙江省', lng: 128.89 },
  { name: '佳木斯',  province: '黑龙江省', lng: 130.37 },
  { name: '七台河',  province: '黑龙江省', lng: 130.86 },
  { name: '牡丹江',  province: '黑龙江省', lng: 129.63 },
  { name: '黑河',    province: '黑龙江省', lng: 127.53 },
  { name: '绥化',    province: '黑龙江省', lng: 126.99 },
  { name: '大兴安岭',province: '黑龙江省', lng: 124.12 },
  // 湖北省
  { name: '武汉',    province: '湖北省',   lng: 114.30 },
  { name: '黄石',    province: '湖北省',   lng: 115.08 },
  { name: '十堰',    province: '湖北省',   lng: 110.80 },
  { name: '宜昌',    province: '湖北省',   lng: 111.29 },
  { name: '襄阳',    province: '湖北省',   lng: 112.14 },
  { name: '鄂州',    province: '湖北省',   lng: 114.90 },
  { name: '荆门',    province: '湖北省',   lng: 112.20 },
  { name: '孝感',    province: '湖北省',   lng: 113.92 },
  { name: '荆州',    province: '湖北省',   lng: 112.24 },
  { name: '黄冈',    province: '湖北省',   lng: 114.90 },
  { name: '咸宁',    province: '湖北省',   lng: 114.32 },
  { name: '随州',    province: '湖北省',   lng: 113.38 },
  { name: '恩施',    province: '湖北省',   lng: 109.49 },
  // 湖南省
  { name: '长沙',    province: '湖南省',   lng: 112.98 },
  { name: '株洲',    province: '湖南省',   lng: 113.13 },
  { name: '湘潭',    province: '湖南省',   lng: 112.94 },
  { name: '衡阳',    province: '湖南省',   lng: 112.61 },
  { name: '邵阳',    province: '湖南省',   lng: 111.47 },
  { name: '岳阳',    province: '湖南省',   lng: 113.13 },
  { name: '常德',    province: '湖南省',   lng: 111.70 },
  { name: '张家界',  province: '湖南省',   lng: 110.48 },
  { name: '益阳',    province: '湖南省',   lng: 112.36 },
  { name: '郴州',    province: '湖南省',   lng: 113.02 },
  { name: '永州',    province: '湖南省',   lng: 111.62 },
  { name: '怀化',    province: '湖南省',   lng: 109.98 },
  { name: '娄底',    province: '湖南省',   lng: 112.00 },
  { name: '湘西',    province: '湖南省',   lng: 109.74 },
  // 吉林省
  { name: '长春',    province: '吉林省',   lng: 125.33 },
  { name: '吉林',    province: '吉林省',   lng: 126.57 },
  { name: '四平',    province: '吉林省',   lng: 124.35 },
  { name: '辽源',    province: '吉林省',   lng: 125.14 },
  { name: '通化',    province: '吉林省',   lng: 125.94 },
  { name: '白山',    province: '吉林省',   lng: 126.43 },
  { name: '松原',    province: '吉林省',   lng: 124.83 },
  { name: '白城',    province: '吉林省',   lng: 122.84 },
  { name: '延边',    province: '吉林省',   lng: 129.51 },
  // 江苏省
  { name: '南京',    province: '江苏省',   lng: 118.77 },
  { name: '无锡',    province: '江苏省',   lng: 120.30 },
  { name: '徐州',    province: '江苏省',   lng: 117.28 },
  { name: '常州',    province: '江苏省',   lng: 119.97 },
  { name: '苏州',    province: '江苏省',   lng: 120.62 },
  { name: '南通',    province: '江苏省',   lng: 120.87 },
  { name: '连云港',  province: '江苏省',   lng: 119.22 },
  { name: '淮安',    province: '江苏省',   lng: 119.02 },
  { name: '盐城',    province: '江苏省',   lng: 120.16 },
  { name: '扬州',    province: '江苏省',   lng: 119.41 },
  { name: '镇江',    province: '江苏省',   lng: 119.45 },
  { name: '泰州',    province: '江苏省',   lng: 119.92 },
  { name: '宿迁',    province: '江苏省',   lng: 118.28 },
  // 江西省
  { name: '南昌',    province: '江西省',   lng: 115.93 },
  { name: '景德镇',  province: '江西省',   lng: 117.21 },
  { name: '萍乡',    province: '江西省',   lng: 113.86 },
  { name: '九江',    province: '江西省',   lng: 116.00 },
  { name: '新余',    province: '江西省',   lng: 114.92 },
  { name: '鹰潭',    province: '江西省',   lng: 117.07 },
  { name: '赣州',    province: '江西省',   lng: 114.94 },
  { name: '吉安',    province: '江西省',   lng: 114.99 },
  { name: '宜春',    province: '江西省',   lng: 114.40 },
  { name: '抚州',    province: '江西省',   lng: 116.36 },
  { name: '上饶',    province: '江西省',   lng: 117.97 },
  // 辽宁省
  { name: '沈阳',    province: '辽宁省',   lng: 123.43 },
  { name: '大连',    province: '辽宁省',   lng: 121.60 },
  { name: '鞍山',    province: '辽宁省',   lng: 122.99 },
  { name: '抚顺',    province: '辽宁省',   lng: 123.96 },
  { name: '本溪',    province: '辽宁省',   lng: 123.77 },
  { name: '丹东',    province: '辽宁省',   lng: 124.38 },
  { name: '锦州',    province: '辽宁省',   lng: 121.13 },
  { name: '营口',    province: '辽宁省',   lng: 122.22 },
  { name: '阜新',    province: '辽宁省',   lng: 121.66 },
  { name: '辽阳',    province: '辽宁省',   lng: 123.19 },
  { name: '盘锦',    province: '辽宁省',   lng: 122.07 },
  { name: '铁岭',    province: '辽宁省',   lng: 123.85 },
  { name: '朝阳',    province: '辽宁省',   lng: 120.45 },
  { name: '葫芦岛',  province: '辽宁省',   lng: 120.84 },
  // 内蒙古自治区
  { name: '呼和浩特',province: '内蒙古自治区', lng: 111.75 },
  { name: '包头',    province: '内蒙古自治区', lng: 109.84 },
  { name: '乌海',    province: '内蒙古自治区', lng: 106.83 },
  { name: '赤峰',    province: '内蒙古自治区', lng: 118.96 },
  { name: '通辽',    province: '内蒙古自治区', lng: 122.26 },
  { name: '鄂尔多斯',province: '内蒙古自治区', lng: 109.78 },
  { name: '呼伦贝尔',province: '内蒙古自治区', lng: 119.77 },
  { name: '巴彦淖尔',province: '内蒙古自治区', lng: 107.39 },
  { name: '乌兰察布',province: '内蒙古自治区', lng: 113.11 },
  { name: '兴安盟',  province: '内蒙古自治区', lng: 122.05 },
  { name: '锡林郭勒',province: '内蒙古自治区', lng: 116.07 },
  { name: '阿拉善',  province: '内蒙古自治区', lng: 105.73 },
  // 宁夏回族自治区
  { name: '银川',    province: '宁夏回族自治区', lng: 106.27 },
  { name: '石嘴山',  province: '宁夏回族自治区', lng: 106.37 },
  { name: '吴忠',    province: '宁夏回族自治区', lng: 106.20 },
  { name: '固原',    province: '宁夏回族自治区', lng: 106.28 },
  { name: '中卫',    province: '宁夏回族自治区', lng: 105.18 },
  // 青海省
  { name: '西宁',    province: '青海省',   lng: 101.78 },
  { name: '海东',    province: '青海省',   lng: 102.40 },
  { name: '海北',    province: '青海省',   lng: 100.90 },
  { name: '黄南',    province: '青海省',   lng: 102.02 },
  { name: '海南',    province: '青海省',   lng: 100.62 },
  { name: '果洛',    province: '青海省',   lng:  99.98 },
  { name: '玉树',    province: '青海省',   lng:  97.01 },
  { name: '海西',    province: '青海省',   lng:  97.36 },
  // 山东省
  { name: '济南',    province: '山东省',   lng: 117.00 },
  { name: '青岛',    province: '山东省',   lng: 120.38 },
  { name: '淄博',    province: '山东省',   lng: 118.06 },
  { name: '枣庄',    province: '山东省',   lng: 117.57 },
  { name: '东营',    province: '山东省',   lng: 118.67 },
  { name: '烟台',    province: '山东省',   lng: 121.39 },
  { name: '潍坊',    province: '山东省',   lng: 119.10 },
  { name: '济宁',    province: '山东省',   lng: 116.59 },
  { name: '泰安',    province: '山东省',   lng: 117.09 },
  { name: '威海',    province: '山东省',   lng: 122.12 },
  { name: '日照',    province: '山东省',   lng: 119.52 },
  { name: '临沂',    province: '山东省',   lng: 118.36 },
  { name: '德州',    province: '山东省',   lng: 116.36 },
  { name: '聊城',    province: '山东省',   lng: 115.99 },
  { name: '滨州',    province: '山东省',   lng: 118.02 },
  { name: '菏泽',    province: '山东省',   lng: 115.48 },
  // 山西省
  { name: '太原',    province: '山西省',   lng: 112.55 },
  { name: '大同',    province: '山西省',   lng: 113.30 },
  { name: '阳泉',    province: '山西省',   lng: 113.58 },
  { name: '长治',    province: '山西省',   lng: 113.12 },
  { name: '晋城',    province: '山西省',   lng: 112.85 },
  { name: '朔州',    province: '山西省',   lng: 112.43 },
  { name: '晋中',    province: '山西省',   lng: 112.76 },
  { name: '运城',    province: '山西省',   lng: 111.01 },
  { name: '忻州',    province: '山西省',   lng: 112.73 },
  { name: '临汾',    province: '山西省',   lng: 111.52 },
  { name: '吕梁',    province: '山西省',   lng: 111.14 },
  // 陕西省
  { name: '西安',    province: '陕西省',   lng: 108.95 },
  { name: '铜川',    province: '陕西省',   lng: 108.96 },
  { name: '宝鸡',    province: '陕西省',   lng: 107.14 },
  { name: '咸阳',    province: '陕西省',   lng: 108.71 },
  { name: '渭南',    province: '陕西省',   lng: 109.51 },
  { name: '延安',    province: '陕西省',   lng: 109.49 },
  { name: '汉中',    province: '陕西省',   lng: 107.03 },
  { name: '榆林',    province: '陕西省',   lng: 109.72 },
  { name: '安康',    province: '陕西省',   lng: 109.02 },
  { name: '商洛',    province: '陕西省',   lng: 109.94 },
  // 四川省
  { name: '成都',    province: '四川省',   lng: 104.07 },
  { name: '自贡',    province: '四川省',   lng: 104.78 },
  { name: '攀枝花',  province: '四川省',   lng: 101.72 },
  { name: '泸州',    province: '四川省',   lng: 105.44 },
  { name: '德阳',    province: '四川省',   lng: 104.40 },
  { name: '绵阳',    province: '四川省',   lng: 104.68 },
  { name: '广元',    province: '四川省',   lng: 105.84 },
  { name: '遂宁',    province: '四川省',   lng: 105.59 },
  { name: '内江',    province: '四川省',   lng: 105.07 },
  { name: '乐山',    province: '四川省',   lng: 103.76 },
  { name: '南充',    province: '四川省',   lng: 106.11 },
  { name: '眉山',    province: '四川省',   lng: 103.85 },
  { name: '宜宾',    province: '四川省',   lng: 104.64 },
  { name: '广安',    province: '四川省',   lng: 106.63 },
  { name: '达州',    province: '四川省',   lng: 107.50 },
  { name: '雅安',    province: '四川省',   lng: 103.00 },
  { name: '巴中',    province: '四川省',   lng: 106.75 },
  { name: '资阳',    province: '四川省',   lng: 104.63 },
  { name: '阿坝',    province: '四川省',   lng: 102.22 },
  { name: '甘孜',    province: '四川省',   lng:  99.96 },
  { name: '凉山',    province: '四川省',   lng: 102.27 },
  // 新疆维吾尔自治区
  { name: '乌鲁木齐',province: '新疆维吾尔自治区', lng:  87.62 },
  { name: '克拉玛依',province: '新疆维吾尔自治区', lng:  84.87 },
  { name: '吐鲁番',  province: '新疆维吾尔自治区', lng:  89.19 },
  { name: '哈密',    province: '新疆维吾尔自治区', lng:  93.52 },
  { name: '昌吉',    province: '新疆维吾尔自治区', lng:  87.30 },
  { name: '博尔塔拉',province: '新疆维吾尔自治区', lng:  82.07 },
  { name: '巴音郭楞',province: '新疆维吾尔自治区', lng:  86.14 },
  { name: '阿克苏',  province: '新疆维吾尔自治区', lng:  80.27 },
  { name: '克孜勒苏',province: '新疆维吾尔自治区', lng:  76.17 },
  { name: '喀什',    province: '新疆维吾尔自治区', lng:  75.99 },
  { name: '和田',    province: '新疆维吾尔自治区', lng:  79.92 },
  { name: '伊犁',    province: '新疆维吾尔自治区', lng:  81.32 },
  { name: '塔城',    province: '新疆维吾尔自治区', lng:  82.98 },
  { name: '阿勒泰',  province: '新疆维吾尔自治区', lng:  88.14 },
  // 西藏自治区
  { name: '拉萨',    province: '西藏自治区', lng: 91.11 },
  { name: '日喀则',  province: '西藏自治区', lng: 88.88 },
  { name: '昌都',    province: '西藏自治区', lng: 97.18 },
  { name: '林芝',    province: '西藏自治区', lng: 94.36 },
  { name: '山南',    province: '西藏自治区', lng: 91.77 },
  { name: '那曲',    province: '西藏自治区', lng: 92.06 },
  { name: '阿里',    province: '西藏自治区', lng: 80.11 },
  // 云南省
  { name: '昆明',    province: '云南省',   lng: 102.73 },
  { name: '曲靖',    province: '云南省',   lng: 103.80 },
  { name: '玉溪',    province: '云南省',   lng: 102.55 },
  { name: '保山',    province: '云南省',   lng:  99.17 },
  { name: '昭通',    province: '云南省',   lng: 103.72 },
  { name: '丽江',    province: '云南省',   lng: 100.23 },
  { name: '普洱',    province: '云南省',   lng: 100.97 },
  { name: '临沧',    province: '云南省',   lng: 100.09 },
  { name: '楚雄',    province: '云南省',   lng: 101.55 },
  { name: '红河',    province: '云南省',   lng: 103.38 },
  { name: '文山',    province: '云南省',   lng: 104.21 },
  { name: '西双版纳',province: '云南省',   lng: 100.80 },
  { name: '大理',    province: '云南省',   lng: 100.27 },
  { name: '德宏',    province: '云南省',   lng:  98.58 },
  { name: '怒江',    province: '云南省',   lng:  98.86 },
  { name: '迪庆',    province: '云南省',   lng:  99.71 },
  // 浙江省
  { name: '杭州',    province: '浙江省',   lng: 120.15 },
  { name: '宁波',    province: '浙江省',   lng: 121.56 },
  { name: '温州',    province: '浙江省',   lng: 120.67 },
  { name: '嘉兴',    province: '浙江省',   lng: 120.75 },
  { name: '湖州',    province: '浙江省',   lng: 120.09 },
  { name: '绍兴',    province: '浙江省',   lng: 120.58 },
  { name: '金华',    province: '浙江省',   lng: 119.65 },
  { name: '衢州',    province: '浙江省',   lng: 118.87 },
  { name: '舟山',    province: '浙江省',   lng: 122.21 },
  { name: '台州',    province: '浙江省',   lng: 121.43 },
  { name: '丽水',    province: '浙江省',   lng: 119.92 },
]

const props = defineProps<{
  modelValue: number | undefined
  optional?: boolean
  initialCity?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: number | undefined]
  'city-change': [info: { cityName: string; province: string; lon: number }]
}>()

const selectedProvince = ref('')
const selectedCity     = ref('')

// 省份列表：直辖市置顶，其余按汉字拼音排序
const provinces = computed<string[]>(() => {
  const fixed = ['北京市', '上海市', '天津市', '重庆市']
  const rest  = [...new Set(CITIES.map(c => c.province))]
    .filter(p => !fixed.includes(p))
    .sort((a, b) => a.localeCompare(b, 'zh'))
  return [...fixed, ...rest]
})

const citiesInProvince = computed<City[]>(() =>
  selectedProvince.value
    ? CITIES.filter(c => c.province === selectedProvince.value)
    : []
)

function onProvinceChange() {
  selectedCity.value = ''
  if (props.optional || !selectedProvince.value) {
    emit('update:modelValue', undefined)
  }
}

function onCityChange() {
  const city = CITIES.find(c => c.name === selectedCity.value)
  if (city) {
    emit('update:modelValue', city.lng)
    emit('city-change', { cityName: city.name, province: city.province, lon: city.lng })
  } else {
    emit('update:modelValue', undefined)
  }
}

function applyCity(cityLabel: string | undefined) {
  if (!cityLabel) return
  const city = CITIES.find(c => c.name === cityLabel)
  if (city) {
    selectedProvince.value = city.province
    selectedCity.value     = city.name
    emit('update:modelValue', city.lng)
  }
}

onMounted(() => applyCity(props.initialCity))

// 当 initialCity prop 变化时（父组件动态传入）同步更新
watch(() => props.initialCity, (newCity) => applyCity(newCity))
</script>

<template>
  <label>出生省份</label>
  <select v-model="selectedProvince" @change="onProvinceChange">
    <option value="">{{ optional ? '不填' : '-- 请选 --' }}</option>
    <option v-for="p in provinces" :key="p" :value="p">{{ p }}</option>
  </select>
  <label class="inner-lbl">城市</label>
  <select
    v-model="selectedCity"
    :disabled="!selectedProvince"
    @change="onCityChange"
  >
    <option value="">{{ selectedProvince ? '-- 请选 --' : '先选省份' }}</option>
    <option v-for="c in citiesInProvince" :key="c.name" :value="c.name">
      {{ c.name }}
    </option>
  </select>
  <span v-if="modelValue !== undefined" class="hint">经度 {{ modelValue.toFixed(2) }}°E</span>
  <span v-else-if="optional" class="hint">选填，用于真太阳时修正</span>
</template>

<style scoped>
select {
  padding: 7px 10px;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  font-size: var(--fs-md);
  background-color: var(--bg-card, #fff);
  cursor: pointer;
}
select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
select:focus {
  outline: none;
  border-color: var(--accent);
}
.inner-lbl {
  width: auto !important;
  margin-left: var(--sp-2, 4px) !important;
  font-size: var(--fs-md);
  color: var(--text-2);
  flex-shrink: 0;
}
.hint {
  color: var(--text-3);
  font-size: var(--fs-sm);
}
</style>
