# -*- coding: utf-8 -*-
from scrapy.spiders import Spider
from scrapy.selector import Selector

from gorden_crawler.items import BaseItem, ImageItem, SkuItem, Color
from scrapy import Request
from scrapy_redis.spiders import RedisSpider
from random import random
from urllib import quote
import logging
import re
import execjs
from gorden_crawler.spiders.shiji_base import BaseSpider

class SixPmSpider(BaseSpider):
#class SixPmSpider(RedisSpider):
    name = "sixpm"
    allowed_domains = ["6pm.com", "elasticbeanstalk.com"]
    
    '''
    正式运行的时候，start_urls为空，通过传参数来进行，通过传递参数 -a 处理
    '''
    start_urls =[ 
        'http://www.6pm.com/womens~1b?s=recentSalesStyle/desc', #women
		'http://www.6pm.com/mens~u?s=isNew/desc/goLiveDate/desc/recentSalesStyle/desc/', #men
		'http://www.6pm.com/girls-clothing~2g',  #girl's clothing
		'http://www.6pm.com/girls-shoes~7?s=goliveRecentSalesStyle/desc/', #girl's shoes
        'http://www.6pm.com/boys-clothing~1p', #boy's clothing
		'http://www.6pm.com/boys-shoes~6?s=isNew/desc/goLiveDate/desc/recentSalesStyle/desc/' #boy's shoes
    ]
    
    custom_settings = {
        #'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
        'DOWNLOAD_TIMEOUT': 20
    }
    
    base_url = 'http://www.6pm.com'

    def handle_parse_item(self, response, item):
        pImgStr = "".join(re.findall(r'(pImgs[^;]+;)+', response.body))
        
        context = execjs.compile('''
            %s
            function getPImgs(){
                return pImgs;
            }
        ''' % pImgStr)
        
        pImgs = context.call('getPImgs')
        
        sel = Selector(response)
        
        stock_json_result = re.search(r'var stockJSON[\s]*=[\s]*([^;]+);', response.body)

        if stock_json_result:
            stock_dic = eval(stock_json_result.group(1))
        
        if stock_dic:
            color_price_dic = eval(re.search(r'colorPrices[\s]*=[\s]*([^;]+);', response.body).group(1))
            style_id_dic = eval(re.search(r'styleIds[\s]*=[\s]*([^;]+);', response.body).group(1))
            product_gender = eval(re.search(r'productGender[\s]*=[\s]*([^;]+);', response.body).group(1))
            zeta_categories = eval(re.search(r'zetaCategories[\s]*=[\s]*([^;]+);', response.body).group(1))
            category = eval(re.search(r'category[\s]*=[\s]*([^;]+);', response.body).group(1))
            sub_category = eval(re.search(r'subCategory[\s]*=[\s]*("[^"]+"[\s]*);', response.body).group(1))
    
            dimension_dic = eval(re.search(r'dimensions[\s]*=[\s]*([^;]+);', response.body).group(1))
            #dimToUnitToValJSON = eval(re.search(r'dimToUnitToValJSON[\s]*=[\s]*([^;]+);', response.body).group(1))
            dimensionIdToNameJson = eval(re.search(r'dimensionIdToNameJson[\s]*=[\s]*([^;]+);', response.body).group(1))
            valueIdToNameJSON = eval(re.search(r'valueIdToNameJSON[\s]*=[\s]*([^;]+);', response.body).group(1))
            colorNames = eval(re.search(r'colorNames[\s]*=[\s]*({[^}]+}[\s]*);', response.body).group(1))
            
            if len(zeta_categories) > 0:
                item['product_type'] =  zeta_categories[0].values()[0]
                
                if category == item['product_type']:
                    item['category'] = sub_category
                else:
                    item['category'] = category
                    item['sub_category'] = sub_category
            else:
                item['product_type'] = category
                item['category'] = sub_category
            
            if 'gender' in response.meta.keys():
                meta_gender = response.meta['gender']
                
                if product_gender.lower == 'unisex':
                    if meta_gender == 'boys' or meta_gender == 'girls':
                        item['gender'] = 'kid-unisex'
                    else:
                        item['gender'] = 'unisex'
                else:
                    item['gender'] = meta_gender
            
            
            '''跳过描述，过于复杂'''
            desc = sel.xpath('//div[@id="productDescription"]//div[@itemprop="description"]/ul').extract()
            item_desc=sel.xpath('//div[@id="prdInfoText"]//span[@class="description summary"]/ul')
            item_desc2=sel.xpath('//div[@id="prdInfoText"]//div[@itemprop="description"]/ul')
            
            size_info_images = []
            
            if len(desc) > 0:
                item['desc'] = desc[0]
                
                size_infos = sel.xpath('//div[@id="productDescription"]//div[@itemprop="description"]/ul/li/a[@class="popup-570-550"]')
                
                if len(size_infos) > 0:
                    size_info_images = []
                    for size_info in size_infos:
                        size_info_image_url = size_info.xpath('@href').extract()[0]
                        
                        if not re.match(r'^http:\/\/', size_info_image_url):
                            size_info_image_url = self.base_url + size_info_image_url
                        size_info_images.append(size_info_image_url)
                
            elif len(item_desc)>0:
                item['desc'] = item_desc.extract()[0]
                
                size_infos = sel.xpath('//div[@id="prdInfoText"]//span[@class="description summary"]/ul/li/a[@class="popup-570-550"]')
                
                if len(size_infos) > 0:
                    size_info_images = []
                    for size_info in size_infos:
                        size_info_image_url = size_info.xpath('@href').extract()[0]
                        if not re.match(r'^http:\/\/', size_info_image_url):
                            size_info_image_url = self.base_url + size_info_image_url
                        size_info_images.append(size_info_image_url)
            elif len(item_desc2) > 0:
                item['desc'] = ''.join(item_desc2.extract())
                
                size_infos = sel.xpath('//div[@id="prdInfoText"]//div[@itemprop="description"]/ul/li/a[@class="popup-570-550"]')
                
                if len(size_infos) > 0:
                    size_info_images = []
                    for size_info in size_infos:
                        size_info_image_url = size_info.xpath('@href').extract()[0]
                        
                        if not re.match(r'^http:\/\/', size_info_image_url):
                            size_info_image_url = self.base_url + size_info_image_url
                        size_info_images.append(size_info_image_url)
            else:
                item['desc'] = ''
              
            if len(size_info_images) > 0:
                item['size_info'] = {'images': size_info_images}  

            colors = []
            '''处理color'''
            for (color,color_name) in colorNames.items():
                colorItem = Color()
                
                colorItem['type'] = 'color'
                colorItem['from_site'] = self.name
                colorItem['show_product_id'] = item['show_product_id']
                colorItem['name'] = color_name
                colors.append(color_name)
                
                styleId = str(style_id_dic[color])
                #colorItem['cover'] = sel.xpath('//a[@id="frontrow-'+color+'"]/img/@src').extract()[0]
                if 'p' in pImgs[styleId]['DETAILED'].keys():
                    colorItem['cover'] = pImgs[styleId]['DETAILED']['p']
                elif 'd' in  pImgs[styleId]['DETAILED'].keys():
                    colorItem['cover'] = pImgs[styleId]['DETAILED']['d']
                elif '1' in pImgs[styleId]['MULTIVIEW_THUMBNAILS'].keys():
                    colorItem['cover'] = pImgs[styleId]['MULTIVIEW_THUMBNAILS']['1']
                else:
                    return
                
                colorImages = pImgs[styleId]
                thumbImages = colorImages['MULTIVIEW_THUMBNAILS']
                images = colorImages['2x']
                if len(images) == 0:
                    images = colorImages['MULTIVIEW']
                
                thumbImages= sorted(thumbImages.iteritems(), key=lambda d:d[0])
                
                images_array = []
                for image_tuple in thumbImages:
                    imageItem = ImageItem()
                    
                    if image_tuple[0] in images.keys():
                        imageItem['image'] = images[image_tuple[0]]
                        imageItem['thumbnail'] = image_tuple[1]

                        if image_tuple[0] == 'p' or image_tuple[0] == 'd':
                            images_array.insert(0, imageItem)
                        else:
                            images_array.append(imageItem)
                    
                colorItem['images'] = images_array
                
                yield colorItem
             
            item['colors'] = colors
            
            dimensions = []
            sizes = {}
            for dimension in dimension_dic:
                dimensions.append(dimensionIdToNameJson[dimension])
                sizes[dimensionIdToNameJson[dimension]] = []
            
            if len(dimensions) == 0:
                dimensions = ['size']
            
            if len(sizes) == 0:
                sizes = {'size' : ['onesize']}
            
            item['dimensions'] = dimensions
                
            '''处理sku库存'''
            skuCollectionsList = []
            for sku_stock in stock_dic:
                
                color = sku_stock['color']
                
                if color in color_price_dic.keys():
                    skuItem = SkuItem()
                    skuItem['type'] = 'sku'
                    skuItem['from_site'] = self.name
                    skuItem['show_product_id'] = item['show_product_id']
                    skuItem['id'] = sku_stock['id']

                    skuItem["list_price"] = color_price_dic[color]['wasInt']
                    skuItem['current_price'] = color_price_dic[color]['nowInt']
                    
                    skuItem['color'] = colorNames[color]
                    
                    size_demension = {}
                    for demension in dimension_dic:
                        if demension in sku_stock.keys() and sku_stock[demension] in valueIdToNameJSON.keys(): 
                            size_value = valueIdToNameJSON[sku_stock[demension]]['value']
                            size_demension[dimensionIdToNameJson[demension]] = size_value
                        
                            if not size_value in  sizes[dimensionIdToNameJson[demension]]:
                                sizes[dimensionIdToNameJson[demension]].append(size_value)
     
                    if len(size_demension) == 0:
                        size_demension = {'size': 'onesize'}
     
                    skuItem['size'] = size_demension
                    skuItem['quantity'] = sku_stock['onHand']
                    skuItem['is_outof_stock'] = False
                    
                    skuCollectionsList.append(skuItem)
                    
            item['skus'] = skuCollectionsList
            item['sizes'] = sizes

            item = self.handle_dimension_to_name(response, item, dimensionIdToNameJson)
            price_url = 'http://stripeswestsixpm.elasticbeanstalk.com/StripesPriceStock/productId/' + str(item['show_product_id'])
            # yield Request(price_url, meta={'item': item, 'colorNames': colorNames, 'skuCollectionsList': skuCollectionsList}, callback=self.parse_price)
            yield item

    def handle_dimension_to_name(self, response, item, dimensionid_to_name):
        dimensionid_to_name['color']= 'color'
        item['dimension_names'] = dimensionid_to_name
        return item

    # def parse_price(self, response):
    #     item = response.meta['item']
    #     colorNames = response.meta['colorNames']
    #     skuCollectionsList = response.meta['skuCollectionsList']
    #     pice_dict = eval(response.body)
    #     if 'error' not in pice_dict.keys() and len(pice_dict) > 0:
    #         for sku in skuCollectionsList:
    #             for key, price in pice_dict['price'].items():
    #                 if key in colorNames and colorNames[key] == sku['color'] and sku['current_price'] != price:
    #                     sku['current_price'] = price
    #     item['skus'] = skuCollectionsList
    #     yield item

    #具体的解析规则
    def parse_item(self, response):
#         item = BaseItem()
#         item['type'] = 'base'
#         item['show_product_id'] = '1209118'
        item = response.meta['item']
        return self.handle_parse_item(response, item)


    def start_requests(self):
        for url in self.start_urls:
            yield Request(url)
    
    #爬虫解析入口函数，用于解析丢入的第一个请求，一般是顶级目录页

    def parse(self, response):
        
        if not 'gender' in response.meta:
            if '/men/' in response.url:
                gender = 'men'
            elif '/women/' in response.url:
                gender = 'women'
            elif 'girls' in response.url:
                gender = 'girls'
            else:
                gender = 'boys'
        else:
            gender = response.meta['gender']
        
        sel = Selector(response)
        '''处理下一页'''
        next_button = sel.xpath('//link[@rel="next"]')

        if len(next_button.extract()) > 0:
            next_uri = next_button.xpath('@href').extract()[0]
            self.log(next_uri, level=logging.WARNING)
            next_url = self.base_url + next_uri

            yield Request(next_url, callback=self.parse, meta={'gender': gender})

        '''处理本页item'''
        item_units = sel.css('.product')

        for item_unit in item_units:
            url = item_unit.xpath('@href').extract()

            if len(url):
                item = BaseItem()
                item['from_site'] = self.name
                url = self.base_url + url[0]
                item['url'] = url
                #item['category'] = category
                #item['sub_category'] = sub_category
                item['brand'] = item_unit.css('.brandName').xpath('text()').extract()[0].strip()
                item['title'] = item_unit.css('.productName').xpath('text()').extract()[0].strip()
                item['cover'] = item_unit.css('.productImg').xpath('@src').extract()[0].strip()
                item['show_product_id'] = item_unit.xpath('@data-product-id').extract()[0]
                item['current_price'] = item_unit.css('.price-6pm').xpath('text()').extract()[0]
                list_price_span = item_unit.css('.discount').xpath('string(.)').re(r'\$(.+)\)')
                if len(list_price_span)>0:
                    item['list_price'] = list_price_span[0]
                else:
                    item['list_price'] = item['current_price']
                item['type'] = 'base'
                yield Request(url, meta={'item':item, 'url': url, 'gender': gender}, callback=self.parse_item)