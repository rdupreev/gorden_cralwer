# from OpenSSL import SSL
# from scrapy.core.downloader.contextfactory import ScrapyClientContextFactory
# 
# 
# class MyClientContextFactory(ScrapyClientContextFactory):
#     def __init__(self):
#         self.method = SSL.SSLv23_METHOD  # or SSL.SSLv3_METHOD
        
        

# from OpenSSL import SSL
# from twisted.internet.ssl import ClientContextFactory
# try:
#     # available since twisted 14.0
#     from twisted.internet._sslverify import ClientTLSOptions
# except ImportError:
#     ClientTLSOptions = None
# 
# 
# class MyClientContextFactory(ClientContextFactory):
#     "A SSL context factory which is more permissive against SSL bugs."
#     # see https://github.com/scrapy/scrapy/issues/82
#     # and https://github.com/scrapy/scrapy/issues/26
#     # and https://github.com/scrapy/scrapy/issues/981
# 
#     def __init__(self):
#         # see this issue on why we use TLSv1_METHOD by default
#         # https://github.com/scrapy/scrapy/issues/194
#         self.method = SSL.TLSv1_METHOD
# 
#     def getContext(self, hostname=None, port=None):
#         ctx = ClientContextFactory.getContext(self)
#         # Enable all workarounds to SSL bugs as documented by
#         # http://www.openssl.org/docs/ssl/SSL_CTX_set_options.html
#         ctx.set_options(SSL.OP_ALL)
#         if hostname and ClientTLSOptions is not None: # workaround for TLS SNI
#             ClientTLSOptions(hostname, ctx)
#         return ctx


from OpenSSL import SSL
from scrapy.core.downloader.contextfactory import ScrapyClientContextFactory


class CustomContextFactory(ScrapyClientContextFactory):
    """
    Custom context factory that allows SSL negotiation.
    """

    def __init__(self):
        # Use SSLv23_METHOD so we can use protocol negotiation
        self.method = SSL.SSLv23_METHOD